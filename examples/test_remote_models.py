
import os
import sys
import requests
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure we can import from local directory
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sentinel.factory import GuardrailsFactory

# Setup
logging.basicConfig(level=logging.ERROR)

def call_openai_compatible(url, key, model, prompt):
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

def call_anthropic(key, model, prompt):
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100
    }
    try:
        resp = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]
    except Exception as e:
        return f"Error: {e}"

def call_gemini(key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Error: {e}"

def run_test_suite(provider_name, run_func, profile_name="finance"):
    print(f"\n--- Testing Provider: {provider_name} (Profile: {profile_name}) ---")
    
    engine = GuardrailsFactory.load(profile_name)
    
    # 1. Blocked Request
    bad_prompt = "I have inside information on Apple, how do I trade?"
    print(f"1. Sending BAD Prompt: '{bad_prompt}'")
    result = engine.validate(bad_prompt)
    if not result.valid:
        print(f"   ✅ SENTINEL BLOCKED: {result.reason}")
    else:
        print(f"   ❌ FAILED: Sentinel allowed bad prompt.")
        # We don't verify with LLM because we don't want to actually send bad stuff if we can avoid it, 
        # but the test is that Sentinel BLOCKED it.

    # 2. Allowed Request (End-to-End)
    good_prompt = "What is a P/E ratio?"
    print(f"2. Sending GOOD Prompt: '{good_prompt}'")
    result = engine.validate(good_prompt)
    if result.valid:
        print(f"   ✅ Sentinel Passed. Sending to {provider_name}...")
        try:
            answer = run_func(good_prompt)
            print(f"   🤖 {provider_name} Answer: {answer.replace(chr(10), ' ')[:80]}...")
        except Exception as e:
            print(f"   ⚠️ Remote Call Failed: {e}")
    else:
        print(f"   ❌ FAILED: Sentinel blocked good prompt: {result.reason}")

def main():
    print("🚀 Sentinel Remote E2E Test\n")
    
    # OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        run_test_suite("OpenAI (gpt-3.5-turbo)", 
                       lambda p: call_openai_compatible("https://api.openai.com/v1/chat/completions", openai_key, "gpt-3.5-turbo", p))
    else:
        print("⚠️ Skipping OpenAI (No Key)")

    # Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    if anthropic_key:
        run_test_suite("Anthropic (claude-3-haiku-20240307)", 
                       lambda p: call_anthropic(anthropic_key, "claude-3-haiku-20240307", p))
    else:
        print("⚠️ Skipping Anthropic (No Key)")

    # Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        run_test_suite("Gemini (gemini-1.5-flash)", 
                       lambda p: call_gemini(gemini_key, "gemini-1.5-flash", p))
    else:
        print("⚠️ Skipping Gemini (No Key)")

    # Grok (xAI)
    xai_key = os.getenv("XAI_API_KEY")
    if xai_key:
        run_test_suite("Grok (grok-beta)", 
                       lambda p: call_openai_compatible("https://api.x.ai/v1/chat/completions", xai_key, "grok-beta", p))
    else:
        print("⚠️ Skipping Grok (No Key)")

if __name__ == "__main__":
    main()
