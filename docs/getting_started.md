# Getting Started with Semantic Sentinel

## Installation

You can install the framework directly into your Python application.

### From Release (Recommended)
```bash
pip install semantic-sentinel
```

### From Source (Development)
```bash
git clone https://github.com/rarenicks/semantic-sentinel.git
cd semantic-sentinel
pip install .
```

---

## Library Usage

The core of Semantic Sentinel is the `GuardrailsFactory`. It allows you to load security profiles and validate user inputs programmatically.

### Basic Example

```python
from sentinel.factory import GuardrailsFactory

# 1. Load a security profile (e.g. Finance, Healthcare)
# Built-in profiles: 'finance', 'healthcare', 'default'
engine = GuardrailsFactory.load("finance")

# 2. Validate user input
input_text = "How do I commit insider trading?"
result = engine.validate(input_text)

if not result.valid:
    print(f"Blocked: {result.reason}")
    # Output: Blocked: Semantic:Intent violation (0.85)
else:
    print("Input is safe.")
```

### Async Usage (FastAPI Example)

Sentinel works great with async web frameworks.

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentinel.factory import GuardrailsFactory

app = FastAPI()
engine = GuardrailsFactory.load("default")

class PromptRequest(BaseModel):
    text: str

@app.post("/validate")
async def check_prompt(req: PromptRequest):
    result = engine.validate(req.text)
    if not result.valid:
        raise HTTPException(status_code=400, detail=f"Policy Violation: {result.reason}")
    return {"status": "safe", "sanitized_text": result.sanitized_text}
```

---

## Running the Standalone Gateway (Docker)

If you prefer a microservice architecture, you can run Sentinel as a standalone API gateway using Docker.

```bash
# 1. Build the image
docker build -t semantic-sentinel .

# 2. Run (Port 8000)
# Pass upstream keys if you want the gateway to proxy valid requests
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e ANTHROPIC_API_KEY=sk-... \
  semantic-sentinel
```

Access the dashboard at **[http://localhost:8000](http://localhost:8000)**.
