import re
from typing import Dict, Optional
from sentinel.core import BaseGuardrail, GuardrailResult

class PIIGuardrail(BaseGuardrail):
    def __init__(self, pii_patterns: Optional[Dict[str, str]] = None):
        # Default patterns if none provided
        self.pii_patterns = pii_patterns or {
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "PHONE": r'\b(\+\d{1,2}\s?)?1?\-?\.?\s?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}\b',
            "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
            "CREDIT_CARD": r'\b(?:\d[ -]*?){13,16}\b'
        }

    def validate(self, text: str) -> GuardrailResult:
        sanitized = text
        redacted_types = []
        
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, sanitized):
                redacted_types.append(pii_type)
                sanitized = re.sub(pattern, f"<{pii_type}_REDACTED>", sanitized)
        
        # PII Redaction is "valid" (allowed), just modified.
        return GuardrailResult(
            valid=True,
            sanitized_text=sanitized,
            reason="PII Redacted" if redacted_types else "No PII found",
            action="redacted" if redacted_types else "none",
            metadata={"redacted_types": redacted_types}
        )
