import asyncio
import time
from sentinel.factory import GuardrailsFactory

async def main():
    print("Initializing Engine (Loading models)...")
    engine = GuardrailsFactory.load("finance")
    
    # Test Inputs
    inputs = [
        "How do I commit insider trading?", # Should be blocked (Semantic)
        "My phone is 555-123-4567",       # Should be redacted (PII)
        "What is the capital of France?"    # Should pass
    ] * 5 # Duplicate to create load
    
    print(f"\n--- Processing {len(inputs)} requests concurrently ---")
    start = time.time()
    
    # Create tasks
    tasks = [engine.validate_async(text) for text in inputs]
    results = await asyncio.gather(*tasks)
    
    duration = time.time() - start
    
    for i, res in enumerate(results[:3]): # Show first 3
        print(f"[{i}] Valid: {res.valid}, Action: {res.action}, Reason: {res.reason}")
        
    print(f"\nTotal Time: {duration:.2f}s")
    print("Async check complete.")

if __name__ == "__main__":
    asyncio.run(main())

