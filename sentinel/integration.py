from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger("sentinel_engine")

try:
    from guardrails import Guard, Validator, register_validator
    from guardrails.validators import FailResult, PassResult, ValidationResult
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False
    # Dummy classes to prevent NameError
    Guard = None
    Validator = object
    def register_validator(*args, **kwargs):
        def decorator(cls):
            return cls
        return decorator
    FailResult = None
    PassResult = None
    ValidationResult = None

# -------------------------------------------------------------------------
# Custom Production Validators (Run Locally, No API Key Required)
# -------------------------------------------------------------------------

@register_validator(name="sentinel/competitor_check", data_type="string")
class CompetitorCheck(Validator):
    """
    Validates that the text does not contain competitor names.
    This is a local, custom implementation of the logic to avoid Hub dependencies.
    """
    def __init__(self, competitors: List[str], on_fail: str = "fix"):
        if not GUARDRAILS_AVAILABLE:
            return
        super().__init__(on_fail=on_fail)
        self.competitors = [c.lower() for c in competitors]

    def validate(self, value: Any, metadata: Dict = {}) -> Any:
        if not GUARDRAILS_AVAILABLE:
            return None
            
        found = []
        val_lower = str(value).lower()
        for comp in self.competitors:
            if comp in val_lower:
                found.append(comp)
        
        if found:
            return FailResult(
                error_message=f"Competitor mentions detected: {', '.join(found)}",
                fix_value=value # Could implement redaction here
            )
        return PassResult()

@register_validator(name="sentinel/toxic_check", data_type="string")
class ToxicCheck(Validator):
    def __init__(self, on_fail: str = "fix"):
        if not GUARDRAILS_AVAILABLE:
            return
        super().__init__(on_fail=on_fail)
        
    def validate(self, value: Any, metadata: Dict = {}) -> Any:
        if not GUARDRAILS_AVAILABLE:
            return None

        # Simple local regex for demo purposes (Pro would use a local model)
        toxic_words = ["stupid", "ugly", "idiot", "dumb"]
        found = [w for w in toxic_words if w in str(value).lower()]
        
        if found:
             return FailResult(
                error_message=f"Toxic language detected: {', '.join(found)}",
                fix_value=value
            )
        return PassResult()

class GuardrailsAIAdapter:
    """
    Adapter for integrating guardrails-ai library validators.
    Uses custom local validators for robust, key-less operation.
    """
    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get("enabled", False)
        self.guard = None
        
        if not self.enabled:
            return

        if not GUARDRAILS_AVAILABLE:
            logger.warning("GuardrailsAI enabled in config but 'guardrails-ai' not installed. Skipping.")
            return

        self._setup_guard(config)

    def _setup_guard(self, config: Dict[str, Any]):
        validators = []
        
        # Competitor Check (Using our Custom Local Class)
        competitors = config.get("competitors", [])
        if competitors:
            try:
                validators.append(CompetitorCheck(competitors=competitors, on_fail="exception"))
                logger.info(f"GuardrailsAI: Added Local CompetitorCheck for {competitors}")
            except Exception as e:
                logger.error(f"Failed to init CompetitorCheck: {e}")

        # Toxic Check (Added Local Config)
        if config.get("toxicity_check", False):
             try:
                validators.append(ToxicCheck(on_fail="exception"))
                logger.info("GuardrailsAI: Added Local ToxicCheck")
             except Exception as e:
                logger.error(f"Failed to init ToxicCheck: {e}")

        if validators:
            self.guard = Guard.from_string(validators=validators)

    def validate(self, prompt: str) -> Optional[str]:
        if not self.enabled or not self.guard:
            return None

        try:
            self.guard.validate(prompt)
            return None
        except Exception as e:
            # Structuring the error message cleanly
            return f"Guardrails Validation Failed: {str(e)}"
