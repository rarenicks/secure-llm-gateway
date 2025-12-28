import yaml
import logging
from typing import Dict, Any, List
from sentinel.engine import GuardrailsEngine
from sentinel.core import BaseGuardrail

# Import Guardrail Implementations
from sentinel.defaults.pii_guardrail import PIIGuardrail
from sentinel.defaults.injection_guardrail import PromptInjectionGuardrail
from sentinel.defaults.secret_guardrail import SecretDetectionGuardrail
from sentinel.topic_guardrail import TopicGuardrail

import os

logger = logging.getLogger("sentinel_factory")

class GuardrailsFactory:
    """
    Factory to create a GuardrailsEngine instance from a YAML configuration file.
    """

    @staticmethod
    def load(profile: str) -> GuardrailsEngine:
        """
        Syntactic sugar to load a profile by name (e.g. 'finance') or path.
        """
        # 1. Check if it's a direct path
        if profile.endswith(".yaml") and os.path.exists(profile):
            return GuardrailsFactory.load_from_file(profile)
        
        # 2. Check for packaged profiles (standard for pip installed)
        try:
            # For Python 3.9+ preferred API
            from importlib import resources
            resource_name = f"{profile}.yaml"
            
            # Using traverasable files API
            files = resources.files('sentinel.profiles')
            profile_path = files.joinpath(resource_name)
            
            if profile_path.is_file():
                with resources.as_file(profile_path) as path:
                    return GuardrailsFactory.load_from_file(str(path))
        except ImportError:
            # Fallback for older python or if importlib is fighting us
            pass
        except Exception as e:
            logger.debug(f"Could not load from package resources: {e}")

        # 3. Check standard config locations (Development/Fallback)
        base_dir = os.getcwd() 
        candidates = [
            os.path.join(base_dir, "sentinel", "profiles", f"{profile}.yaml"), # New location dev
            os.path.join(base_dir, "configs", f"{profile}.yaml"), # Old location fallback, might be empty now
            os.path.join(base_dir, "configs", "custom", f"{profile}.yaml"), # Custom still lives here?
        ]

        for p in candidates:
            if os.path.exists(p):
                return GuardrailsFactory.load_from_file(p)
        
        raise FileNotFoundError(f"Could not find profile '{profile}' in package or {candidates}")

    @staticmethod
    def load_from_file(config_path: str) -> GuardrailsEngine:
        """
        Loads a YAML config and creates the v2.0 Engine.
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loading Sentinel Profile: {config.get('profile_name', 'Unknown')}")
            return GuardrailsEngine(config)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            # Return safe default or re-raise?
            # Creating a minimal safe config
            fallback = {
                "profile_name": "FALLBACK",
                "detectors": {"injection": {"enabled": True}}
            }
            return GuardrailsEngine(fallback)


        # 1. Injection (Always critical, usually first)
        if detectors.get("injection", {}).get("enabled", False):
            keywords = detectors["injection"].get("keywords", [])
            target_guardrails.append(PromptInjectionGuardrail(keywords=keywords if keywords else None))

        # 2. Secrets
        if detectors.get("secrets", {}).get("enabled", False):
            # patterns currently hardcoded in class defaults or could be passed if structure aligned
            target_guardrails.append(SecretDetectionGuardrail())

        # 3. Topics (Content blocking)
        if detectors.get("topics", {}).get("enabled", False):
            block_list = detectors["topics"].get("block_list", [])
            target_guardrails.append(TopicGuardrail(block_list=block_list))

        # 4. PII (Sanitization)
        if detectors.get("pii", {}).get("enabled", False):
            # The PIIGuardrail implementation uses a Dict[name, pattern].
            # The config typically provides a list of names to enabled (patterns: ["EMAIL", ...])
            # We can modify PIIGuardrail to accept a list of enabled keys and use internal defaults, 
            # OR generic pattern config. 
            # Our current PIIGuardrail expects a dict or uses ALL defaults. 
            # Let's use ALL defaults for now as per current implementation, 
            # or filtering by list if we enhance PIIGuardrail later.
            # Simplified for MVP: Use default patterns.
            target_guardrails.append(PIIGuardrail())

        return GuardrailsEngine(guardrails=target_guardrails)
