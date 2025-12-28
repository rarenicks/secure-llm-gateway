import re
from typing import Dict, Optional, List
from sentinel.core import BaseGuardrail, GuardrailResult

class SecretDetectionGuardrail(BaseGuardrail):
    """
    Detects and blocks common API keys and secrets.
    """
    def __init__(self, patterns: Optional[Dict[str, str]] = None):
        self.secret_patterns = patterns or {
            "AWS Ability Key": r'(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])', 
            "AWS Secret Key": r'(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])', 
            "OpenAI Key": r'sk-[a-zA-Z0-9]{32,}', 
            "Generic Private Key": r'-----BEGIN PRIVATE KEY-----',
            "GitHub Token": r'ghp_[a-zA-Z0-9]{36}',
            "Google Service Account": r'"type":\s*"service_account"',
            "Google API Key": r'AIza[0-9A-Za-z\\-_]{35}',
            "Slack Token": r'xox[baprs]-([0-9a-zA-Z]{10,48})?',
            "Stripe Secret": r'(sk|rk)_live_[0-9a-zA-Z]{24}',
            "Env File Pattern": r'(?m)^[A-Z_]+=(?!=).*$' # Matches KEY=VALUE on a new line (heuristic)
        }

    def validate(self, text: str) -> GuardrailResult:
        found_secrets = []
        
        for name, pattern in self.secret_patterns.items():
            if re.search(pattern, text):
                found_secrets.append(name)
        
        if found_secrets:
            return GuardrailResult(
                valid=False,
                sanitized_text=text, # Don't return secrets even in sanitized if blocking, but here we return original for debugging context usually
                reason=f"Secrets detected: {', '.join(found_secrets)}",
                action="blocked"
            )
            
        return GuardrailResult(
            valid=True,
            sanitized_text=text,
            reason="No secrets found",
            action="allowed"
        )
