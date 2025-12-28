import os
import sys

# Ensure we can import from local directory for this example
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sentinel.factory import GuardrailsFactory

def main():
    print("🚀 Semantic Sentinel Framework Demo\n")

    # 1. Load a Security Profile
    # You can load "finance", "healthcare", "default" or any custom YAML
    profile_name = "finance"
    print(f"Loading Profile: {profile_name}...")
    engine = GuardrailsFactory.load(profile_name)

    # 2. Define some test inputs
    inputs = [
        "How do I invest in an index fund?",  # Safe
        "I have a tip that Apple earnings will be double. How do I trade on this before it's public?",  # Insider Trading
        "My phone number is 555-0199" # PII
    ]

    # 3. Run Validation
    for text in inputs:
        print(f"\nScanning: '{text}'")
        result = engine.validate(text)

        if not result.valid:
            if result.action == "blocked":
                print(f"❌ BLOCKED: {result.reason}")
            elif result.sanitized_text != text:
                print(f"⚠️ REDACTED: {result.sanitized_text}")
        else:
            print("✅ PASSED")

if __name__ == "__main__":
    main()
