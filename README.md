# Secure GenAI Gateway

A robust, enterprise-grade security proxy for Large Language Models (LLMs) built with **FastAPI**. It intercepts, sanitizes, and routes requests to multiple providers (OpenAI, Anthropic, Gemini, Grok) while providing real-time security visualization.

## 🚀 Key Features

- **🛡️ Real-time Guardrails**: 
    - **PII Redaction**: Automatically detects and replaces sensitive info (Emails, Phones) with `<REDACTED>` tags.
    - **Injection Blocking**: Stops jailbreak attempts (e.g., "Ignore previous instructions") instantly.
- **⚡ Multi-Provider Routing**: Seamlessly route to OpenAI, Anthropic (Claude), Google (Gemini), xAI (Grok), or Local LLMs based on the model name.
- **📊 Interactive Dashboard**:
    - **Live Chat Interface**: Chat with any supported model.
    - **Security Stream**: Watch requests get scanned and blocked in real-time.
    - **Visual Feedback**: Premium toast notifications when PII is intercepted.
- **📝 Audit Logging**: Asynchronous SQLite logging of every request, verdict, and latency.

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
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### 🖥️ Dashboard
Open **[http://localhost:8000](http://localhost:8000)** to access the Real-time Security Dashboard.

## 🧪 Verification

Run the automated test suite to verify routing and security logic:
```bash
python verify_proxy.py
```

## ✅ Compliance Verification

The **Semantic Sentinel** engine is rigorously tested against adversarial datasets. Below is a snapshot of the **Compliance Runner** blocking 100% of Money Laundering and Financial Crime attempts:

![Compliance Verification](assets/compliance_verification.png)

*Generated via `tools/compliance_runner.py` using `configs/finance.yaml`.*

## 📂 Architecture

- **`app/main.py`**: Entry point & API routes.
- **`app/core/`**:
    - `guardrails.py`: Security engine (Regex/Heuristics).
    - `router.py`: Intelligent provider routing.
    - `logger.py`: Audit logging system.
- **`app/static/`**: Frontend assets (HTML/CSS/JS).

## License

MIT License
