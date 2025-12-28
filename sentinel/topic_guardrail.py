from typing import List, Optional
import re
from sentinel.core import BaseGuardrail, GuardrailResult

class TopicGuardrail(BaseGuardrail):
    """
    Blocks content related to specific topics or keywords.
    """
    def __init__(self, block_list: Optional[List[str]] = None):
        self.block_list = block_list or []
        # Create a compiled regex for performance
        if self.block_list:
            # Escape keywords to avoid regex meta-char issues
            pattern_str = r'\b(' + '|'.join(map(re.escape, self.block_list)) + r')\b'
            self.pattern = re.compile(pattern_str, re.IGNORECASE)
        else:
            self.pattern = None

    def validate(self, text: str) -> GuardrailResult:
        if not self.pattern:
            return GuardrailResult(valid=True, sanitized_text=text, reason="No topics configured", action="allowed")

        matches = self.pattern.findall(text)
        if matches:
            unique_matches = sorted(list(set(matches)))
            return GuardrailResult(
                valid=False,
                sanitized_text=text,
                reason=f"Restricted topic detected: {', '.join(unique_matches)}",
                action="blocked"
            )

        return GuardrailResult(
            valid=True,
            sanitized_text=text,
            reason="Passed topic check",
            action="allowed"
        )
