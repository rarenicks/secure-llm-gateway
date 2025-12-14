from typing import List
from .core import BaseGuardrail, GuardrailResult

class GuardrailsEngine:
    """
    Engine to manage and execute a pipeline of guardrails.
    """
    
    def __init__(self, guardrails: List[BaseGuardrail] = None):
        self.guardrails = guardrails or []

    def add_guardrail(self, guardrail: BaseGuardrail):
        self.guardrails.append(guardrail)

    def validate(self, text: str) -> GuardrailResult:
        """
        Runs the text through all registered guardrails sequentially.
        If any guardrail blocks the request (valid=False), execution stops and returns that result.
        Otherwise, the text is sanitized by each guardrail in order.
        """
        current_text = text
        
        for guardrail in self.guardrails:
            result = guardrail.validate(current_text)
            
            if not result.valid:
                # If blocked, return immediately
                return result
            
            # If valid, pass the sanitized text to the next guardrail
            current_text = result.sanitized_text
            
        return GuardrailResult(
            valid=True,
            sanitized_text=current_text,
            reason="Passed all guardrails",
            action="allowed"
        )
