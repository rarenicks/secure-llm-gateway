from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BasePlugin(ABC):
    """
    Abstract Base Class for External Security Plugins.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", False)

    @abstractmethod
    def scan(self, text: str) -> Optional[str]:
        """
        Scans text and returns an error message if violated, or None if safe.
        """
        pass
