from typing import Dict, Any
from guardrails_lib.core import BaseGuardrail, GuardrailResult

class CustomGuardrail(BaseGuardrail):
    """
    Template for a custom guardrail.
    Use this as a starting point to implement your own security logic.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize your guardrail with optional configuration.
        """
        self.config = config or {}

    def validate(self, text: str) -> GuardrailResult:
        """
        Your custom validation logic goes here.
        """
        
        # Example Logic: Block if specific custom logic fails
        if "BLOCK_ME" in text:
            return GuardrailResult(
                valid=False,
                sanitized_text=text,
                reason="Custom logic triggered block",
                action="blocked"
            )
        
        # Example Logic: Sanitize / Modify text
        sanitized = text.replace("UNSAFE", "SAFE")
        
        return GuardrailResult(
            valid=True,
            sanitized_text=sanitized,
            reason="Passed custom checks",
            action="allowed"
        )
