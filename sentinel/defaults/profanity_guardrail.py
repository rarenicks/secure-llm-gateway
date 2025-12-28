from typing import List, Optional
import re
from sentinel.core import BaseGuardrail, GuardrailResult

class ProfanityGuardrail(BaseGuardrail):
    """
    Blocks or redacts toxic language.
    Default behavior is to BLOCK.
    """
    def __init__(self, bad_words: Optional[List[str]] = None, mode: str = "block"):
        self.mode = mode # 'block' or 'redact'
        self.bad_words = bad_words or [
            "badword",
            "offensive",
            "toxic",
            "violence"
        ]
        # Create a compiled regex for performance
        self.pattern = re.compile(r'\b(' + '|'.join(map(re.escape, self.bad_words)) + r')\b', re.IGNORECASE)

    def validate(self, text: str) -> GuardrailResult:
        if self.mode == "block":
            matches = self.pattern.findall(text)
            if matches:
                return GuardrailResult(
                    valid=False,
                    sanitized_text=text,
                    reason=f"Profanity detected: {', '.join(set(matches))}",
                    action="blocked"
                )
        elif self.mode == "redact":
            sanitized = self.pattern.sub(lambda m: "*" * len(m.group()), text)
            if sanitized != text:
                 return GuardrailResult(
                    valid=True,
                    sanitized_text=sanitized,
                    reason="Profanity redacted",
                    action="redacted"
                )

        return GuardrailResult(
            valid=True,
            sanitized_text=text,
            reason="Clean content",
            action="allowed"
        )
