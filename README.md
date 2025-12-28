# Semantic Sentinel Gateway (v2.0)

A robust, enterprise-grade security proxy for Large Language Models (LLMs) built with **FastAPI**. It intercepts, sanitizes, and routes requests to multiple providers (OpenAI, Anthropic, Gemini, Grok) while providing real-time security visualization and semantic analysis.


## 🚀 Key Features

- **🧠 Semantic Intent Analysis**: Uses local embeddings (`sentence-transformers`) to block adversarial attacks based on *intent* (e.g., "Money Laundering", "Insider Trading") rather than just keywords.
- **🛡️ Real-time Guardrails**: 
    - **PII Redaction**: Automatically detects and replaces sensitive info (Emails, Phones) with `<REDACTED>` tags.
    - **Injection Blocking**: Stops jailbreak attempts (e.g., "Ignore previous instructions") instantly.
    - **Topic Filtering**: Configurable regex blocking for domain-specific keywords.
- **🔄 Dynamic Security Profiles**: Switch between different security policies (e.g., Finance, Healthcare, Default) instantly via the UI without restarting.
- **⚡ Multi-Provider Routing**: Seamlessly route to OpenAI, Anthropic (Claude), Google (Gemini), xAI (Grok), or Local LLMs based on the model name.
- **📊 Interactive Dashboard**:
    - **Live Chat Interface**: Chat with any supported model.
    - **Security Stream**: Watch requests get scanned and blocked in real-time.
    - **Visual Feedback**: Premium toast notifications when PII is intercepted.
- **📝 Audit Logging**: Asynchronous SQLite logging of every request, verdict, and latency.
- **📉 Compliance Reporting**: Automated tools to stress-test your guardrails and generate JSON audits with pass/fail rates.

## 🛠️ Quick Start

### Prerequisites
- Python 3.10+
- (Optional) API Keys for OpenAI/Anthropic/Gemini/Grok

### Installation

1. **Clone & Setup**:
   ```bash
   git clone https://github.com/rarenicks/secure-llm-gateway.git
   cd secure-llm-gateway
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Copy `.env` and add your keys:
   ```env
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Run the Gateway**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 🖥️ Dashboard
Open **[http://localhost:8000](http://localhost:8000)** to access the Real-time Security Dashboard.

---

## 🧠 Semantic Guardrails (How it Works)

Unlike traditional WAFs that block based on keywords (e.g., "bomb", "fraud"), **Semantic Sentinel** understands the *meaning* of a prompt.

1. **Embeddings**: We use a local, quantized model (`all-MiniLM-L6-v2`) to convert user prompts into vector embeddings.
2. **Cosine Similarity**: The system calculates the distance between the user's prompt and your defined `forbidden_intents`.
3. **Thresholding**: If the similarity score exceeds your configured threshold (e.g., `0.25`), the request is blocked.

**Example**:
- **Rule**: Block "Money Laundering"
- **User Prompt**: "How can I clean the cash from my unregistered business?" (No keywords like "laundering" used).
- **Result**: **BLOCKED** (Similarity Score: 0.58).

---

## 🦙 Local LLM Support (Ollama / LocalAI)

The gateway supports local inference out of the box.

1. **Run Ollama**:
   ```bash
   ollama serve
   ollama pull llama3
   ```

2. **Connect Gateway**:
   By default, the gateway routes unknown models to `http://localhost:11434/v1/chat/completions`.
   
   To use a custom URL, add this to your `.env`:
   ```env
   TARGET_LLM_URL=http://localhost:8080/v1/chat/completions
   ```

3. **Chat**:
   In the dashboard, simply type **`llama3`** (or your local model name) into the model field. The gateway will automatically route requests to your local instance while still applying all security guardrails.

---

## 🔧 Extending for Your Domain

Semantic Sentinel is designed to be **Configuration-Driven**. You can create custom security profiles for specific use cases (e.g., Legal, HR, Finance) by creating simple YAML files.

### 1. Create a Config File
Create a new file in `configs/my_domain.yaml`:

```yaml
name: "My_Domain_Policy_v1"

guardrails:
  pii:
    enabled: true  # Redact Email, Phone, SSN
    
  topics:
    enabled: true
    blacklist:
      - "competitor_name"
      - "proprietary_project_code"
      
  semantic_blocking:
    enabled: true
    threshold: 0.25 # Lower = Stricter (0.0 to 1.0)
    forbidden_intents:
      - "violating company nda"
      - "leaking trade secrets"
      - "harassment or toxicity"
```

### 2. Activate Your Profile
1. Go to the dashboard at `http://localhost:8000`.
2. Use the **Security Profile** dropdown in the sidebar.
3. Select `my_domain.yaml`.
4. Your new rules are now live!

---

## 🧪 Testing & Auditing

### Manual Testing with Chatbot
Use the built-in chat interface to attempt "red teaming" your setup.
- **Try Valid Inputs**: "Write a summary of..." (Should PASS)
- **Try PII**: "My email is test@example.com" (Should show `<REDACTED>`)
- **Try Attacks**: "Tell me how to violate the NDA" (Should be **BLOCKED** with a system warning).

### Automated Compliance Runner
For enterprise validation, use the included compliance tool to run a dataset of prompts against your active profile.

1. **Create a Test Dataset** (`tests/data/compliance.csv`):
   ```csv
   prompt,expected
   "How do I file legal taxes?",passed
   "How do I evade taxes?",blocked
   ```

2. **Run the Audit**:
   ```bash
   python tools/compliance_runner.py tests/data/compliance.csv
   ```
   
### 3. View Report:
   A detailed `compliance_report.json` will be generated with pass/fail statistics and latency metrics.

---

## 🧱 Hybrid Architecture (Pro)

We support a **Dual-Engine** approach, combining our high-speed internal engine with the ecosystem of **Guardrails AI**.

**1. Semantic Sentinel Engine (Internal)**:
- **Speed**: <50ms latency.
- **Role**: Handles PII redaction, regex patterns, and semantic embedding checks.

**2. Guardrails AI (External Library)**:
- **Role**: Access to specialized community validators.
- **Integration**: We implemented a custom `GuardrailsAIAdapter` that runs local, key-less validators:
    - `CompetitorCheck`: Blocks mentions of "Google", "OpenAI" etc.
    - `ToxicCheck`: Blocks toxicity using local logic.

To enable this, use `configs/hybrid.yaml`.

---

## ✅ Compliance Verification

The **Semantic Sentinel** engine is rigorously tested against adversarial datasets. Below is a snapshot of the **Compliance Runner** blocking 100% of Money Laundering and Financial Crime attempts:

![Compliance Verification](assets/compliance_verification.png)

*Generated via `tools/compliance_runner.py` using `configs/finance.yaml`.*

## 📂 Architecture

- **`app/main.py`**: Entry point & API routes.
- **`guardrails_lib/`**:
    - `engine.py`: The core Semantic & Regex analysis engine.
    - `factory.py`: Dynamic config loader.
- **`configs/`**: YAML security definitions.
- **`tools/`**: Compliance and stress testing scripts.

## 📦 Development & Deployment

### Running Unit Tests
We use `pytest` for unit and integration testing.
```bash
# Run all tests
./run_tests.sh
```

### Docker Support
Build and run the gateway in a container:
```bash
# Build image
docker build -t semantic-sentinel .

# Run container (port 8000)
docker run -p 8000:8000 semantic-sentinel
```

## License

MIT License
