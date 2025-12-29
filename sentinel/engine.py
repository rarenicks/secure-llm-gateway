from typing import List, Dict, Any, Optional
import re
import logging
import asyncio
import time
from sentinel.core import BaseGuardrail, GuardrailResult
from sentinel.topic_guardrail import TopicGuardrail
from sentinel.integration import GuardrailsAIAdapter
from sentinel.presidio_adapter import PresidioAdapter
from sentinel.plugins.langkit_plugin import LangKitPlugin
from sentinel.audit import BaseAuditLogger, NullAuditLogger

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

logger = logging.getLogger("sentinel_engine")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

class GuardrailsEngine:
    """
    v2.0 Semantic Sentinel Engine
    - Pre-compiled Regex (Performance)
    - Semantic Analysis (Sentence Transformers)
    - PII Redaction (Regex or Presidio)
    - Injection & Leakage Protection
    - Pluggable Architecture (LangKit, etc.)
    - Async Support
    - Audit Logging & Shadow Mode
    """

    def __init__(self, config: Dict[str, Any], audit_logger: Optional[BaseAuditLogger] = None):
        self.config = config
        self.detectors = config.get("detectors", {})
        self.profile_name = config.get("profile_name", "Unknown")
        self.shadow_mode = config.get("shadow_mode", False)
        self.audit_logger = audit_logger or NullAuditLogger()
        
        if self.shadow_mode:
            logger.warning(f"[{self.profile_name}] SHADOW MODE ENABLED. Violations will be logged but NOT blocked.")

        # --- 1. PII Redaction (Regex vs Presidio) ---
        self.pii_enabled = self.detectors.get("pii", {}).get("enabled", False)
        self.pii_engine_type = self.detectors.get("pii", {}).get("engine", "regex")
        
        self.pii_patterns = []
        self.presidio = None

        if self.pii_enabled:
            if self.pii_engine_type == "presidio":
                # Initialize Enterprise Presidio
                self.presidio = PresidioAdapter()
                if not self.presidio.enabled:
                    logger.warning("Presidio requested but not available. Falling back to Regex.")
                    self.pii_engine_type = "regex"
                else:
                    logger.info(f"[{self.profile_name}] PII: Using Enterprise Presidio Engine.")
            
            if self.pii_engine_type == "regex":
                # Fallback / Standard Regex
                patterns = {
                    "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                    "PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
                    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
                    "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
                }
                enabled_keys = self.detectors["pii"].get("patterns", [])
                for key in enabled_keys:
                    if key in patterns:
                        self.pii_patterns.append((key, re.compile(patterns[key])))
                logger.info(f"[{self.profile_name}] PII: Compiled {len(self.pii_patterns)} regex patterns.")

        # --- 2. Pre-compile Topic/Keyword Patterns ---
        self.topic_pattern = None
        if self.detectors.get("topics", {}).get("enabled", False):
            block_list = self.detectors["topics"].get("block_list", [])
            if block_list:
                pattern_str = r'\b(' + '|'.join(map(re.escape, block_list)) + r')\b'
                self.topic_pattern = re.compile(pattern_str, re.IGNORECASE)
                logger.info(f"[{self.profile_name}] Topics: Compiled regex with {len(block_list)} keywords.")

        # --- 3. Injection & Prompt Leakage ---
        self.injection_patterns = []
        if self.detectors.get("injection", {}).get("enabled", False):
            # Combined list of injection and leakage patterns
            defaults = [
                "ignore previous instructions", "ignore all instructions",
                "system override", "dan mode", "do anything now", "unfiltered",
                "jailbreak", "developer mode", "system prompt", "original instructions"
            ]
            custom = self.detectors["injection"].get("keywords", [])
            all_keywords = list(set(defaults + custom))
            if all_keywords:
                pattern_str = r'\b(' + '|'.join(map(re.escape, all_keywords)) + r')\b'
                self.injection_patterns.append(re.compile(pattern_str, re.IGNORECASE))
                logger.info(f"[{self.profile_name}] Injection: Compiled regex with {len(all_keywords)} keywords.")

        # --- 4. Initialize Semantic Model ---
        self.semantic_model = None
        self.forbidden_embeddings = None
        self.semantic_threshold = 0.0
        self.forbidden_intents = []
        
        # Base Jailbreak intents that are always checked if semantic analysis is enabled
        self.BASE_JAILBREAK_INTENTS = [
            "ignore previous instructions",
            "jailbreak attempt",
            "bypassing safety guardrails",
            "revealing system prompt",
            "acting as an unfiltered AI",
            "performing restricted actions"
        ]
        
        semantic_cfg = self.detectors.get("semantic_blocking", {})
        if semantic_cfg.get("enabled", False):
            if not SEMANTIC_AVAILABLE:
                logger.warning("Semantic blocking enabled but 'sentence-transformers' not installed. Skipping.")
            else:
                try:
                    logger.info("Loading Semantic Model (all-MiniLM-L6-v2)...")
                    self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                    
                    intents = semantic_cfg.get("forbidden_intents", [])
                    # Merge with base jailbreak intents for comprehensive protection
                    self.forbidden_intents = list(set(intents + self.BASE_JAILBREAK_INTENTS))
                    
                    if self.forbidden_intents:
                        self.forbidden_embeddings = self.semantic_model.encode(self.forbidden_intents)
                        self.semantic_threshold = semantic_cfg.get("threshold", 0.45) # Default to a conservative 0.45 if enabled
                        logger.info(f"[{self.profile_name}] Semantic: Encoded {len(self.forbidden_intents)} intents. Threshold: {self.semantic_threshold}")
                except Exception as e:
                    logger.error(f"Failed to load Semantic Model: {e}")

        # --- 5. External Guardrails AI ---
        external_config = config.get("guardrails", {}).get("external_hub", {})
        self.external_guard = GuardrailsAIAdapter(external_config)

        # --- 6. Dynamic Plugins ---
        self.plugins = []
        self._load_plugins(config.get("plugins", {}))


    def _load_plugins(self, plugins_config: Dict[str, Any]):
        """
        Dynamically load supported plugins.
        """
        # 1. LangKit
        langkit_cfg = plugins_config.get("langkit", {})
        if langkit_cfg.get("enabled", False):
            self.plugins.append(LangKitPlugin(langkit_cfg))

    def validate(self, text: str) -> GuardrailResult:
        """
        Validates INPUT text (Synchronous).
        """
        start_time = time.time()
        result_dict = self.scan(text, source="input")
        duration_ms = (time.time() - start_time) * 1000
        
        final_result = self._package_result(result_dict)
        
        # Audit Log
        self.audit_logger.log({
            "profile": self.profile_name,
            "source": "input",
            "valid": final_result.valid,
            "action": final_result.action,
            "reason": final_result.reason,
            "latency_ms": duration_ms,
            "shadow_mode": self.shadow_mode,
            "input_len": len(text)
        })
        
        return final_result
        
    async def validate_async(self, text: str) -> GuardrailResult:
        """
        Validates INPUT text (Asynchronous).
        """
        start_time = time.time()
        result_dict = await self.scan_async(text, source="input")
        duration_ms = (time.time() - start_time) * 1000
        
        final_result = self._package_result(result_dict)

        # Audit Log (Async safe since loggers are usually sync I/O or threaded)
        # For high-scale, logger should be non-blocking too, but File/Console is fine here.
        self.audit_logger.log({
            "profile": self.profile_name,
            "source": "input",
            "valid": final_result.valid,
            "action": final_result.action,
            "reason": final_result.reason,
            "latency_ms": duration_ms,
            "shadow_mode": self.shadow_mode,
            "input_len": len(text)
        })
        
        return final_result

    def validate_output(self, text: str) -> GuardrailResult:
        """
        Validates OUTPUT text (Synchronous).
        """
        start_time = time.time()
        result_dict = self.scan(text, source="output")
        duration_ms = (time.time() - start_time) * 1000
        
        final_result = self._package_result(result_dict)

        self.audit_logger.log({
            "profile": self.profile_name,
            "source": "output",
            "valid": final_result.valid,
            "action": final_result.action,
            "reason": final_result.reason,
            "latency_ms": duration_ms,
            "shadow_mode": self.shadow_mode,
            "input_len": len(text)
        })

        return final_result

    def _package_result(self, result: Dict[str, Any]) -> GuardrailResult:
        triggered = result["triggered_rules"]
        is_valid = len(triggered) == 0
        sanitized = result["sanitized_prompt"]
        reason = ", ".join(triggered) if not is_valid else ""
        
        action = "allowed"
        if not is_valid:
            pii_only = all(t.startswith("PII:") for t in triggered)
            if pii_only:
                is_valid = True
                reason = "PII Redacted"
                action = "redacted"
            else:
                action = "blocked"
                
                # SHADOW MODE LOGIC
                if self.shadow_mode:
                    # In shadow mode, we return VALID even if blocked.
                    # We keep the 'reason' populated for the caller to know it *would* have been blocked.
                    is_valid = True
                    action = "shadow_block" 
                    # We do NOT return sanitized text in shadow mode? 
                    # Actually, usually you want to see if it works, so returning original might be better.
                    # Let's return original text to be safe in shadow mode.
                    # Wait, 'sanitized' might contain PII redactions. PII redaction usually IS desired even in shadow mode?
                    # "Shadow Mode" typically refers to BLOCKING policies. PII redaction is a transform.
                    # Let's assume PII redaction still happens (it's "valid" anyway), but BLOCKS are ignored.
                    
                    # If it was a block (not just PII), revert sanitized text to potentially unsafe original? 
                    # No, safer to return the analyzed version but mark valid. 
                    # BUT, if semantic block triggers, 'sanitized_prompt' is essentially the input.
                    pass
        
        return GuardrailResult(
            valid=is_valid,
            sanitized_text=sanitized,
            reason=reason,
            action=action
        )

    def scan(self, prompt: str, source: str = "input") -> Dict[str, Any]:
        """
        v2.0 Optimized Scan Pipeline (Synchronous)
        """
        triggered = []
        sanitized_prompt = prompt
        semantic_score = 0.0

        # Step 1: PII Redaction
        if self.pii_enabled:
            if self.presidio and self.presidio.enabled:
                sanitized_prompt, pii_types = self.presidio.scan_and_redact(sanitized_prompt)
                if pii_types:
                    triggered.extend(pii_types)
            else:
                for name, pattern in self.pii_patterns:
                    if pattern.search(sanitized_prompt):
                        msg = f"<{name}_REDACTED>"
                        sanitized_prompt = pattern.sub(msg, sanitized_prompt)
                        triggered.append(f"PII:{name}")

        # Step 2: Injection/Leakage (Input Only)
        if source == "input" and self.injection_patterns:
            for pat in self.injection_patterns:
                if pat.search(sanitized_prompt):
                    triggered.append("Injection:System Prompt Override")

        # Step 3: Keyword Blocking (Topics)
        if self.topic_pattern:
            matches = self.topic_pattern.findall(sanitized_prompt)
            if matches:
                unique = sorted(list(set(matches)))
                triggered.append(f"Topic:{','.join(unique)}")

        # Step 4: Semantic Blocking (Input Only)
        if source == "input" and self.semantic_model and self.forbidden_embeddings is not None:
            prompt_emb = self.semantic_model.encode([sanitized_prompt])
            scores = cosine_similarity(prompt_emb, self.forbidden_embeddings)[0]
            max_index = scores.argmax()
            max_score = float(scores[max_index])
            semantic_score = max_score
            
            if max_score > self.semantic_threshold:
                matched_intent = self.forbidden_intents[max_index]
                triggered.append(f"Semantic:Intent violation (matched '{matched_intent}', score {max_score:.2f})")
            
            logger.info(f"Semantic Check ({source}): MaxScore={max_score:.4f} Intent='{self.forbidden_intents[max_index]}' Threshold={self.semantic_threshold}")

        # Step 5: External & Plugins (Skipped for brevity in sync, usually fast enough or omitted)
        if self.external_guard.enabled and source == "input":
            ext_error = self.external_guard.validate(sanitized_prompt)
            if ext_error:
                triggered.append(f"External: {ext_error}")

        for plugin in self.plugins:
            err = plugin.scan(sanitized_prompt)
            if err:
                 triggered.append(f"Plugin:{err}")

        return {
            "sanitized_prompt": sanitized_prompt,
            "triggered_rules": triggered,
            "semantic_score": semantic_score
        }

    async def scan_async(self, prompt: str, source: str = "input") -> Dict[str, Any]:
        """
        Async Scan Pipeline
        Offloads CPU-bound tasks (Presidio, Embeddings) to executors.
        """
        triggered = []
        sanitized_prompt = prompt
        semantic_score = 0.0
        loop = asyncio.get_running_loop()

        # Step 1: PII Redaction
        if self.pii_enabled:
            if self.presidio and self.presidio.enabled:
                # Async Presidio Call
                sanitized_prompt, pii_types = await self.presidio.scan_and_redact_async(sanitized_prompt)
                if pii_types:
                    triggered.extend(pii_types)
            else:
                # Regex is fast enough to keep sync usually, but could offload if massive text
                for name, pattern in self.pii_patterns:
                    if pattern.search(sanitized_prompt):
                        msg = f"<{name}_REDACTED>"
                        sanitized_prompt = pattern.sub(msg, sanitized_prompt)
                        triggered.append(f"PII:{name}")

        # Step 2: Injection (Regex, fast)
        if source == "input" and self.injection_patterns:
            for pat in self.injection_patterns:
                if pat.search(sanitized_prompt):
                    triggered.append("Injection:System Prompt Override")

        # Step 3: Topics (Regex, fast)
        if self.topic_pattern:
            matches = self.topic_pattern.findall(sanitized_prompt)
            if matches:
                unique = sorted(list(set(matches)))
                triggered.append(f"Topic:{','.join(unique)}")

        # Step 4: Semantic Blocking (CPU Bound)
        if source == "input" and self.semantic_model and self.forbidden_embeddings is not None:
            # Run encoding in thread pool
            def _compute_semantic():
                prompt_emb = self.semantic_model.encode([sanitized_prompt])
                scores = cosine_similarity(prompt_emb, self.forbidden_embeddings)[0]
                return scores
            
            scores = await loop.run_in_executor(None, _compute_semantic)
            max_index = scores.argmax()
            max_score = float(scores[max_index])
            semantic_score = max_score
            
            if max_score > self.semantic_threshold:
                matched_intent = self.forbidden_intents[max_index]
                triggered.append(f"Semantic:Intent violation (matched '{matched_intent}', score {max_score:.2f})")
            
            logger.info(f"Semantic Check ({source}) [Async]: MaxScore={max_score:.4f}")

        # Step 5 & 6: External/Plugins (Assuming sync for now, can be made async if plugins support it)
        # ... (Same as sync)
        for plugin in self.plugins:
            err = plugin.scan(sanitized_prompt)
            if err:
                 triggered.append(f"Plugin:{err}")

        return {
            "sanitized_prompt": sanitized_prompt,
            "triggered_rules": triggered,
            "semantic_score": semantic_score
        }