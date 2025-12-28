# Contributing to Secure GenAI Gateway

We welcome contributions! Whether you're fixing bugs, improving documentation, or creating new plugins, your help is appreciated.

## 🛠️ Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/rarenicks/secure-llm-gateway.git
   cd secure-llm-gateway
   ```

2. **Create a Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   # Install Spacy model for PII tests
   python -m spacy download en_core_web_lg
   ```

## 🧪 Running Tests

We use `pytest` for ensuring stability.

```bash
# Run all tests
./run_tests.sh

# Run specific plugin tests
pytest tests/test_plugins.py
```

## 🔌 Creating a New Plugin

1. Create a new file in `guardrails_lib/plugins/`.
2. Inherit from `BasePlugin`.
3. Implement the `scan(text)` method.
4. Add your plugin to `configs/plugins_demo.yaml` to test.

## 📝 Style Guide

- We use **Python 3.10+**.
- Please add type hints (`typing`) to all functions.
- Run `verify_enterprise_deps.py` to ensure new dependencies don't break the build.
