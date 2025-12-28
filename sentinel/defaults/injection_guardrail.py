from typing import List, Optional
from sentinel.core import BaseGuardrail, GuardrailResult

class PromptInjectionGuardrail(BaseGuardrail):
    def __init__(self, keywords: Optional[List[str]] = None):
        self.injection_keywords = keywords or [
            "ignore previous instructions",
            "ignore all instructions",
            "system override",
            "dan mode",
            "do anything now",
            "unfiltered",
            "jailbreak"
        ]

    def validate(self, text: str) -> GuardrailResult:
        lower_text = text.lower()
        for keyword in self.injection_keywords:
            if keyword in lower_text:
                return GuardrailResult(
                    valid=False,
                    sanitized_text=text,
                    reason=f"Prompt Injection Detected: '{keyword}'",
                    action="blocked"
                )
        
        return GuardrailResult(
            valid=True,
            sanitized_text=text,
            reason="Passed Injection Check",
            action="allowed"
        )
