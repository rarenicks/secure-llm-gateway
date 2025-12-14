import os
import re
from typing import Tuple, Dict

class LLMRouter:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        # Support both standard and user-defined var names
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.xai_key = os.getenv("XAI_API_KEY", "")
        self.local_url = os.getenv("TARGET_LLM_URL", "http://localhost:11434/v1/chat/completions")

    def get_route(self, model: str) -> Tuple[str, Dict[str, str], str]:
        """
        Determines the destination API based on the model name.
        Returns: (url, headers, adapter_type)
        """
        model = model.lower()

        # 1. OpenAI
        if model.startswith("gpt-") or model.startswith("o1-"):
            return (
                "https://api.openai.com/v1/chat/completions",
                {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"},
                "openai"
            )

        # 2. Anthropic (Claude)
        if model.startswith("claude-"):
            return (
                "https://api.anthropic.com/v1/messages",
                {
                    "x-api-key": self.anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                "anthropic"
            )

        # 3. Google Gemini
        if model.startswith("gemini-"):
            # Gemini URL requires the key in the query param or header. We'll handle key in adapter or header.
            # Using standard REST API v1beta
            return (
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}",
                {"Content-Type": "application/json"},
                "gemini"
            )

        # 4. xAI (Grok)
        if model.startswith("grok-"):
            return (
                "https://api.x.ai/v1/chat/completions",
                {"Authorization": f"Bearer {self.xai_key}", "Content-Type": "application/json"},
                "openai" # Grok is OpenAI compatible
            )

        # 5. Fallback (Local)
        # Assumes local is OpenAI compatible (Ollama, LocalAI)
        return (
            self.local_url,
            {"Content-Type": "application/json"}, # Local usually no auth
            "openai"
        )
