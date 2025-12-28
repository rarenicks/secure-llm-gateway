# Secure GenAI Gateway & Sentinel Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Package](https://img.shields.io/badge/pypi-v0.0.1-blue.svg)](https://pypi.org/project/semantic-sentinel/)

A production-ready, enterprise-grade security framework for Large Language Models (LLMs). Use it as a **Standalone Gateway** (Docker) or import it as a **Python Library** (`sentinel`) to build your own AI firewalls.

![Security Stream](assets/security_stream_v5.png)

## 🐍 Python Library Usage

Install the framework directly into your Python application:

```bash
pip install .   # Install from source
# OR
pip install semantic-sentinel  # (Coming soon to PyPI)
```

```python
from sentinel.factory import GuardrailsFactory

# 1. Load a security profile (e.g. Finance, Healthcare)
engine = GuardrailsFactory.load("finance")

# 2. Validate user input
input_text = "How do I commit insider trading?"
result = engine.validate(input_text)

if not result.valid:
    print(f"Blocked: {result.reason}")
    # Output: Blocked: Semantic:Intent violation (0.85)
```

---

## 🚀 Key Features

### 🛡️ Core Protections
- **Semantic Intent Blocking**: Blocks adversarial attacks based on *intent* (e.g., "Money Laundering", "Insider Trading") using local embeddings (`sentence-transformers`), catching what keywords miss.
- **Enterprise PII Redaction**:
    - **Microsoft Presidio**: Context-aware redaction (NER) for high-accuracy masking of Names, Locations, and Dates.
    - **Regex Fallback**: High-speed pattern matching for Credit Cards, SSNs, and Phones.
- **Injection & Jailbreak Defense**: Instantly blocks prompts like "Ignore previous instructions" or "DAN Mode".

### 🔌 Extensibility & Plugins
- **Plugin Architecture**: Extend functionality with Python plugins.
    - **LangKit Integration**: Real-time toxicity scoring and injection analysis using `whylogs[langkit]`.
    - **Custom Validators**: Write your own checks in `guardrails_lib/plugins/`.

### 🎓 Educational UI & Experimentation
- **Profile Inspector (ℹ️)**: Visualize active rules for any profile directly in the UI.
- **Custom Profile Builder (+)**: Create, test, and save custom security configs (YAML) via the web interface.
- **Live Audit Stream**: Watch requests get scanned, redacted, and blocked in real-time.

### 🔄 Dynamic Security Profiles
Values encoded in **YAML** files. Switch policies instantly without restarts:
- **`finance.yaml`**: Strict insider trading & financial PII rules.
- **`healthcare.yaml`**: HIPAA-aligned (Medical Record redaction).
- **`presidio_pro.yaml`**: Spacy/Presidio-powered NLP analysis.

## ✨ Feature Matrix

| Category | Feature | Description |
|----------|---------|-------------|
| **Security** | **Semantic Blocking** | Blocks requests based on intent (e.g., "crime") even without keywords. |
| | **PII Redaction** | Context-aware removal of Phones, Emails, SSNs, and Names. |
| | **Injection Defense** | Prevents "jailbreak" attempts and prompt leakage. |
| | **Secret Detection** | Stops API keys and credentials from leaking upstream. |
| | **Profanity Filter** | Sanitizes offensive language from inputs. |
| **Connectivity** | **Multi-Provider** | Route to OpenAI, Anthropic, Gemini, Grok, or Local LLMs. |
| | **Local Fallback** | Seamlessly integrates with Ollama/LocalAI for private inference. |
| **Observability** | **Real-time Dashboard** | Live view of all traffic, blocks, and latency metrics. |
| | **Audit Logging** | SQLite database tracking every request verdict. |
| | **Toast Notifications** | Immediate visual feedback when PII is intercepted. |
| **Extensibility** | **Plugin System** | Add Python plugins (e.g., LangKit) for custom logic. |
| | **YAML Configuration** | No-code policy management via profile files. |
| | **Custom Builder** | Create and test new profiles directly in the UI. |

---

---

## 🛠️ Quick Start

### Option 1: Docker (Recommended)
Getting started is as simple as running a container. We bundle Spacy models and all dependencies.

```bash
# 1. Build the image
docker build -t secure-llm-gateway .

# 2. Run (Port 8000)
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e ANTHROPIC_API_KEY=sk-... \
  secure-llm-gateway
```

Access the dashboard at **[http://localhost:8000](http://localhost:8000)**.

### Option 2: Local Python Dev
```bash
git clone https://github.com/rarenicks/secure-llm-gateway.git
cd secure-llm-gateway

# Setup Venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download Spacy Model for Presidio
python -m spacy download en_core_web_lg

# Run
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧠 Semantic Guardrails (How it Works)

1. **Embeddings**: We use a local, quantized model (`all-MiniLM-L6-v2`) to convert user prompts into vector embeddings.
2. **Cosine Similarity**: The system calculates the distance between the user's prompt and your defined `forbidden_intents` (e.g., "Violating Safety Protocols").
3. **Thresholding**: If the similarity score exceeds your configured threshold (e.g., `0.25`), the request is blocked.

**Example**:
- **Rule**: Block "Money Laundering"
- **User Prompt**: "How can I clean the cash from my unregistered business?" (No keywords like "laundering" used).
- **Result**: **BLOCKED** (Similarity Score: 0.58).

---

## 🔧 Configuration Guide

Security profiles are YAML files. You can use the built-in profiles (like `finance`, `healthcare`) or load your own custom file.

**Loading a built-in profile:**
```python
engine = GuardrailsFactory.load("finance")
```

**Loading a custom profile:**
```python
engine = GuardrailsFactory.load("/path/to/my_policy.yaml")
```

**Example Profile (`my_policy.yaml`):**
```yaml
profile_name: "Corporate_Policy_v1"
description: "Blocks competitor mentions and protects source code."

detectors:
  pii:
    enabled: true
    engine: "presidio" # or "regex"
  
  injection:
    enabled: true
    
  semantic_blocking:
    enabled: true
    threshold: 0.25
    forbidden_intents:
      - "leaking source code"
      - "disparaging competitors"
      
plugins:
  langkit:
    enabled: true
    modules: ["toxicity", "injections"]
```

---

## 🧪 Verification & Testing

We include a suite of tools to verify compliance.

**1. Automated Compliance Runner**:
Run a dataset of attacks against your gateway to generate a pass/fail report.
```bash
python tools/compliance_runner.py tests/data/library_attacks.csv
```

**2. Plugin Verification**:
Ensure LangKit and Presidio are correctly installed.
```bash
python tools/verify_enterprise_deps.py
```

---

## 📂 Project Structure

- **`app/`**: FastAPI Backend & UI Static files.
- **`sentinel/`**: The core Python library.
    - `engine.py`: Core logic combining Regex, Semantics, and Plugins.
    - `presidio_adapter.py`: Interface to Microsoft Presidio.
    - `profiles/`: Built-in YAML security definitions (bundled with package).
    - `plugins/`: Extensible plugin system.
- **`tools/`**: Verification scripts and compliance runners.

## License

MIT License. Built for the Open Source Community.
