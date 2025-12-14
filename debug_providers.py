import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")

print(f"Gemini Key Present: {bool(GEMINI_KEY)}")
print(f"Claude Key Present: {bool(CLAUDE_KEY)}")

def check_gemini():
    if not GEMINI_KEY:
        print("Skipping Gemini (No Key)")
        return

    print("\n--- Checking Gemini Models ---")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            models = res.json().get('models', [])
            print("Available Gemini Models:")
            for m in models:
                if 'generateContent' in m['supportedGenerationMethods']:
                    print(f" - {m['name']}")
        else:
            print(f"Error listing Gemini models: {res.status_code} {res.text}")
    except Exception as e:
        print(f"Gemini Exception: {e}")

def check_claude():
    if not CLAUDE_KEY:
        print("Skipping Claude (No Key)")
        return

    print("\n--- Checking Claude Connectivity ---")
    # Anthropic doesn't have a simple public list endpoint auth'd same way, we'll try a completion with a likely model
    models_to_test = ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
    
    for model in models_to_test:
        print(f"Testing {model}...")
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": CLAUDE_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": model,
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Hi"}]
        }
        try:
            res = requests.post(url, json=data, headers=headers)
            if res.status_code == 200:
                print(f"SUCCESS: {model} is working.")
                break
            else:
                print(f"FAILED {model}: {res.status_code} {res.text}")
        except Exception as e:
            print(f"Claude Exception: {e}")

if __name__ == "__main__":
    check_gemini()
    check_claude()
