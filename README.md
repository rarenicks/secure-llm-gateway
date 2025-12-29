
<h1 align="center">Semantic Sentinel</h1>

![Semantic Sentinel Banner](https://raw.githubusercontent.com/rarenicks/semantic-sentinel/main/assets/semantic_sentinel_banner.png)

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/release/python-3100/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+"></a>
  <a href="https://pypi.org/project/semantic-sentinel/"><img src="https://img.shields.io/badge/pypi-v1.0.0-blue.svg" alt="Package"></a>
  <a href="https://pepy.tech/project/semantic-sentinel"><img src="https://static.pepy.tech/badge/semantic-sentinel" alt="Downloads"></a>
</p>

<p align="center">
A production-ready, enterprise-grade security framework for Large Language Models (LLMs). Use it as a <strong>Standalone Gateway</strong> (Docker) or import it as a <strong>Python Library</strong> (<code>sentinel</code>) to build your own AI firewalls.
</p>

---

## 📦 Installation

### From PyPI (Library Usage)
```bash
pip install semantic-sentinel
```

### From Source (Development)
```bash
git clone https://github.com/rarenicks/semantic-sentinel.git
cd semantic-sentinel
pip install -e .
```

---

## 📚 Documentation

Detailed guides and references:

- 🚀 **[Getting Started](https://github.com/rarenicks/semantic-sentinel/blob/main/docs/getting_started.md)**: Installation and quick start guide.
- ⚙️ **[Configuration Reference](https://github.com/rarenicks/semantic-sentinel/blob/main/docs/configuration.md)**: Deep dive into YAML security profiles.
- 🔌 **[Plugins & Extensibility](https://github.com/rarenicks/semantic-sentinel/blob/main/docs/plugins.md)**: Using LangKit and custom validators.

## 📦 Installation

```bash
# Core installation (Lightweight)
pip install semantic-sentinel

# With specific integrations
pip install "semantic-sentinel[openai,langchain]"

# With advanced plugins (LangKit, Detoxify)
pip install "semantic-sentinel[plugins]"

# Install everything
pip install "semantic-sentinel[all]"
```

## 🐍 Python Library Usage

```python
from sentinel import GuardrailsFactory, download_spacy_model

# 0. (First Run Only) Download necessary models for PII redaction
# download_spacy_model("en_core_web_lg")

# 1. Load a security profile (e.g. Finance, Healthcare)
engine = GuardrailsFactory.load("finance")

# 2. Validate user input
input_text = "How do I commit insider trading?"
result = engine.validate(input_text)

if not result.valid:
    print(f"Blocked: {result.reason}")
    # Output: Blocked: Semantic:Intent violation (matched 'insider trading', score 0.85)
```

### 🔄 Async Support

```python
import asyncio

async def validate_concurrent():
    engine = GuardrailsFactory.load("default")
    
    # Process multiple requests concurrently
    tasks = [
        engine.validate_async("What is AI?"),
        engine.validate_async("My SSN is 123-45-6789"),
    ]
    
    results = await asyncio.gather(*tasks)
    return results

asyncio.run(validate_concurrent())
```

### 🌊 Streaming Sanitization

```python
from sentinel.streaming import StreamSanitizer

engine = GuardrailsFactory.load("finance")
sanitizer = StreamSanitizer(engine)

# Process streaming LLM output
for token in llm_stream:
    for safe_text in sanitizer.process(token):
        print(safe_text, end="", flush=True)

# Don't forget to flush!
for safe_text in sanitizer.flush():
    print(safe_text, end="")
```

---

## 🔗 Framework Integrations

### OpenAI Integration

```python
from sentinel.integrations.openai import SentinelAsyncOpenAI

engine = GuardrailsFactory.load("finance")
client = SentinelAsyncOpenAI(engine=engine, api_key=os.getenv("OPENAI_API_KEY"))

# Automatic input validation and output sanitization
response = await client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    stream=True  # Real-time streaming support!
)

async for chunk in response:
    print(chunk.choices[0].delta.content, end="")
```

Install: `pip install semantic-sentinel[openai]`

### LangChain Integration

```python
from sentinel.integrations.langchain import SentinelRunnable
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

engine = GuardrailsFactory.load("finance")
sentinel = SentinelRunnable(engine=engine)
llm = ChatOpenAI()

# Build chains with pipe syntax
extract = RunnableLambda(lambda x: x['sanitized_text'])
chain = sentinel | extract | llm

result = chain.invoke("What is AI?")  # Validated before LLM!
```

Install: `pip install semantic-sentinel[langchain]`

### LlamaIndex Integration (RAG)

```python
from sentinel.integrations.llamaindex import SentinelNodePostprocessor

engine = GuardrailsFactory.load("finance")
processor = SentinelNodePostprocessor(engine=engine)

# Sanitize retrieved context in RAG pipelines
query_engine = index.as_query_engine(
    node_postprocessors=[processor]
)

response = query_engine.query("Tell me about our financial data")
```

Install: `pip install semantic-sentinel[llamaindex]`

---

## 🚀 Key Features

#### 🏢 Enterprise Features

#### Audit Logging
Record every interaction, verdict, and latency for compliance.
```python
from sentinel.audit import FileAuditLogger

# Logs to 'sentinel_audit.jsonl' for Splunk/Datadog ingestion
audit_logger = FileAuditLogger("audit_logs.jsonl")
engine = GuardrailsFactory.load("finance", audit_logger=audit_logger)
```

#### Shadow Mode (Dry Run)
Test new security policies in production without blocking users.
```yaml
# In your profile.yaml
profile_name: "Finance_v1"
shadow_mode: true  # Detect and log, but do not block
```
Violations will be allowed (valid=True) but marked as `shadow_block` in logs.

### 🤖 HuggingFace Integration
Real-time sanitization for local model generation.
```python
from sentinel.integrations.huggingface import SentinelHFStreamer

streamer = SentinelHFStreamer(tokenizer, engine)
model.generate(..., streamer=streamer)

for token in streamer:
    print(token, end="") # Sanitized!
```

### 💻 CLI Usage
```bash
# Scan text directly
sentinel scan --text "Buy some stocks now" --profile finance

# List available profiles
sentinel list
```

### 🔌 Extensibility & Integrations
- **Framework Support**: Native integrations for OpenAI, LangChain, and LlamaIndex
    - **OpenAI Wrapper**: Drop-in replacement for `openai.OpenAI` with automatic guardrails
    - **LangChain Runnable**: Chain guardrails into your LangChain pipelines
    - **LlamaIndex Postprocessor**: Sanitize RAG context before LLM processing
- **Plugin Architecture**: Extend functionality with Python plugins
    - **LangKit Integration**: Real-time toxicity scoring using `whylogs[langkit]`
    - **Custom Validators**: Write your own checks in `sentinel/plugins/`
- **Async/Streaming**: Full async support with `validate_async()` and `StreamSanitizer`

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

## 📸 Screenshots

### Security Dashboard - Blocked Request
![Dashboard showing blocked request](https://raw.githubusercontent.com/rarenicks/semantic-sentinel/main/assets/dashboard_blocked.png)

### Compliance Verification
![Compliance verification results](https://raw.githubusercontent.com/rarenicks/semantic-sentinel/main/assets/compliance_verification.png)

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
