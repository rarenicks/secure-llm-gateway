# Plugins & Extensibility

Semantic Sentinel v4.5+ introduces a Plugin Architecture. This allows you to integrate external libraries or write custom Python validators.

## Whylogs LangKit

We typically integrate [LangKit](https://github.com/whylabs/langkit) for advanced quality and safety metrics.

### Configuration
Enable it in your profile YAML:

```yaml
plugins:
  langkit:
    enabled: true
    threshold: 0.5
    modules: ["toxicity", "injections"]
```

- **`toxicity`**: Detects toxic language, hate speech, etc.
- **`threshold`**: If the score returned by LangKit is higher than this, the request is blocked.

---

## Guardrails AI (Hybrid Mode)

We also support [Guardrails AI](https://github.com/guardrails-ai/guardrails) validators. This effectively allows Semantic Sentinel to act as a "Meta-Guardrail", orchestrating both local checks and community validators.

### Configuration

```yaml
group: "hybrid_policy"

# Custom config for the adapter
guardrails_ai:
  enabled: true
  competitors: ["CompetitorA", "CompetitorB"] # Uses CompetitorCheck validator
  toxicity_check: true
```

---

## Writing Custom Plugins

You can extend the `BasePlugin` class to create your own logic.

### 1. Create Plugin Class

Create a file `sentinel/plugins/my_custom_plugin.py`:

```python
from typing import Optional
from sentinel.plugins.base import BasePlugin

class MyCustomPlugin(BasePlugin):
    def scan(self, text: str) -> Optional[str]:
        if "secret_codeword" in text:
            return "Custom Plugin Violation: Secret codeword detected"
        return None
```

### 2. Register Plugin

Update `sentinel/engine.py` to import and initialize your plugin based on the config. (Dynamic registration coming in v6.5).
