import logging
from typing import Dict, Any, Optional
from sentinel.plugins.base import BasePlugin

logger = logging.getLogger("sentinel_langkit")

try:
    # Importing submodules if available
    from langkit import toxicity
    LANGKIT_AVAILABLE = True
except ImportError:
    LANGKIT_AVAILABLE = False

class LangKitPlugin(BasePlugin):
    """
    Plugin for Whylogs LangKit (Quality & Safety Metrics).
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.threshold = config.get("threshold", 0.5)
        
        if self.enabled and not LANGKIT_AVAILABLE:
            logger.warning("LangKit enabled but library not found. Plugin disabled.")
            self.enabled = False
        
        if self.enabled:
            logger.info(f"LangKit Plugin Initialized (Threshold: {self.threshold})")

    def scan(self, text: str) -> Optional[str]:
        if not self.enabled:
            return None

        try:
            # Real Implementation using Detoxify via LangKit
            # We treat the model loading as "lazy" or check if it's already cached?
            # Ideally initialize in __init__, but for now putting it here or lazily
            if not hasattr(self, 'model'):
                # Initialize lazily to avoid startup delay if not used
                self.model = toxicity.DetoxifyModel(model_name="original")
            
            # Predict returns a scalar score for "toxicity"
            score = self.model.predict(text)
            
            if score > self.threshold:
                logger.warning(f"LangKit Violation: Toxicity Score {score:.2f} > {self.threshold}")
                return f"LangKit: Toxicity detected ({score:.2f})"
            
            return None

        except Exception as e:
            logger.error(f"LangKit Scan Error: {e}")
            return None