# Configuration Reference

Security profiles in Semantic Sentinel are defined using **YAML**. This allows you to switch policies instantly without changing code.

## Loading Profiles

You can load built-in profiles or custom files:

```python
# Built-in
engine = GuardrailsFactory.load("finance")

# Custom File
engine = GuardrailsFactory.load("/path/to/my_policy.yaml")
```

---

## Profile Structure

A profile YAML consists of metadata and a list of `detectors` or `plugins`.

### Example Profile

```yaml
profile_name: "Corporate_Policy_v1"
description: "Blocks competitor mentions and protects source code."

detectors:
  # 1. PII Redaction
  pii:
    enabled: true
    engine: "presidio" # Options: "regex" (fast) or "presidio" (smart)
    
  # 2. Prompt Injection
  injection:
    enabled: true
    
  # 3. Topic/Keyword Blocking
  topics:
    enabled: true
    forbidden_topics:
      - "political_campaigns"
      - "competitor_product_names"
    
  # 4. Semantic Intent Blocking (The brain)
  semantic_blocking:
    enabled: true
    threshold: 0.25  # Lower = stricter (0.0 to 1.0)
    forbidden_intents:
      - "leaking source code"
      - "disparaging competitors"
      - "insider trading"

# 5. External Plugins
plugins:
  langkit:
    enabled: true
    threshold: 0.7
    modules: ["toxicity"]
```

---

## Detector Modules

### `pii` (Personal Identifiable Information)
- **`engine`**: 
    - `"regex"`: Uses strict patterns (Credit Cards, SSNs, Emails). Extremely fast.
    - `"presidio"`: Uses Microsoft Presidio + Spacy NER. Context-aware (names, locations). Slower but more accurate.

### `semantic_blocking`
Uses **Sentence Transformers** (`all-MiniLM-L6-v2`) to embed your `forbidden_intents` and the user's prompt. It calculates cosine similarity.
- **`threshold`**: A score between 0 and 1. If similarity > threshold, the request is blocked.
    - `0.1`: Very strict (triggers easily).
    - `0.8`: Very loose (only exact matches).
    - Recommended: `0.25 - 0.40`.

### `injection`
Heuristic-based detection for "Jailbreak" attempts (e.g., "Ignore previous instructions", "DAN mode").

### `topics`
Simple keyword matching. Efficient for blocking specific known terms (e.g., Project names).
