import yaml
import logging
import os
from typing import Dict, Any, List, Optional
from sentinel.engine import GuardrailsEngine

logger = logging.getLogger("sentinel_factory")

class GuardrailsFactory:
    """
    Factory to create a GuardrailsEngine instance from a YAML configuration file.
    """

    @staticmethod
    def load(profile: str, audit_logger: Optional[Any] = None) -> GuardrailsEngine:
        """
        Syntactic sugar to load a profile by name (e.g. 'finance') or path.
        """
        # 1. Check if it's a direct path
        if profile.endswith(".yaml") and os.path.exists(profile):
            return GuardrailsFactory.load_from_file(profile, audit_logger=audit_logger)
        
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
                    return GuardrailsFactory.load_from_file(str(path), audit_logger=audit_logger)
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
                return GuardrailsFactory.load_from_file(p, audit_logger=audit_logger)
        
        raise FileNotFoundError(f"Could not find profile '{profile}' in package or local path.")

    @staticmethod
    def load_from_file(config_path: str, audit_logger: Optional[Any] = None) -> GuardrailsEngine:
        """
        Loads a YAML config and creates the v2.0 Engine.
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loading Sentinel Profile: {config.get('profile_name', 'Unknown')}")
            return GuardrailsEngine(config, audit_logger=audit_logger)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            # Minimal safe config
            fallback = {
                "profile_name": "FALLBACK",
                "detectors": {"injection": {"enabled": True}}
            }
            return GuardrailsEngine(fallback)
