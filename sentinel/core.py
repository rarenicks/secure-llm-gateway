from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel

class GuardrailResult(BaseModel):
    valid: bool
    sanitized_text: str
    reason: Optional[str] = None
    action: Optional[str] = None
    metadata: Dict[str, Any] = {}

class BaseGuardrail(ABC):
    """
    Abstract Base Class for all Guardrails.
    Users must implement the `validate` method.
    """
    
    @abstractmethod
    def validate(self, text: str) -> GuardrailResult:
        """
        Validates and potentially sanitizes the input text.
        
        Args:
            text (str): The input prompt from the user.
            
        Returns:
            GuardrailResult: The result of the validation.
        """
        pass
