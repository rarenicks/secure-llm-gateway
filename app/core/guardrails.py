import re
from typing import List, Optional
from pydantic import BaseModel

class GuardrailResult(BaseModel):
    valid: bool
    sanitized_text: str
    reason: Optional[str] = None
    action: Optional[str] = None

class GuardrailsEngine:
    def __init__(self):
        # PII Regex Patterns
        self.pii_patterns = {
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Modified to match 7 to 15 digits including separators.
            # Matches: (123) 456-7890, 123-456-7890, 123 456 7890, +1 123 456 7890
            "PHONE": r'\b(\+\d{1,2}\s?)?1?\-?\.?\s?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}\b',
            "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
            # Simple credit card regex (generic)
            "CREDIT_CARD": r'\b(?:\d[ -]*?){13,16}\b'
        }
        
        # Jailbreak / Injection Keywords
        self.injection_keywords = [
            "ignore previous instructions",
            "ignore all instructions",
            "system override",
            "dan mode",
            "do anything now",
            "unfiltered",
            "jailbreak"
        ]

    def redact_pii(self, text: str) -> str:
        """Scans and redacts PII from the text."""
        sanitized = text
        for pii_type, pattern in self.pii_patterns.items():
            sanitized = re.sub(pattern, f"<{pii_type}_REDACTED>", sanitized)
        return sanitized

    def check_injection(self, text: str) -> bool:
        """Checks for prompt injection attempts. Returns True if injection detected."""
        lower_text = text.lower()
        for keyword in self.injection_keywords:
            if keyword in lower_text:
                return True
        return False

    def validate(self, text: str) -> GuardrailResult:
        """
        Main entry point for validation.
        1. Check for Injections (Blocking).
        2. Redact PII (Sanitizing).
        """
        # 1. Check Injection
        if self.check_injection(text):
            return GuardrailResult(
                valid=False,
                sanitized_text=text, # No need to sanitize if blocked, but keeping original for context if needed
                reason="Prompt Injection Detected",
                action="blocked"
            )

        # 2. Redact PII
        sanitized_text = self.redact_pii(text)
        
        return GuardrailResult(
            valid=True,
            sanitized_text=sanitized_text,
            reason="Passed",
            action="allowed"
        )
