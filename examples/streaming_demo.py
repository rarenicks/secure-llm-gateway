import time
from sentinel.factory import GuardrailsFactory
from sentinel.streaming import StreamSanitizer

def mock_llm_stream():
    """Simulates an LLM yielding tokens."""
    tokens = [
        "Hello", " there!", " My", " phone", " number", " is", " 555", "-", "0199", ".",
        " I", " want", " to", " commit", " insider", " trading", " now", "."
    ]
    for t in tokens:
        time.sleep(0.05) # Simulate network delay
        yield t

def main():
    print("Initializing Engine...")
    # Load 'finance' profile which likely blocks 'insider trading'
    engine = GuardrailsFactory.load("finance")
    sanitizer = StreamSanitizer(engine)
    
    print("\n--- Starting Stream ---")
    
    full_output = ""
    
    for token in mock_llm_stream():
        # Process token through sanitizer
        # Note: sanitizer.process returns a generator, so we iterate it
        for safe_chunk in sanitizer.process(token):
            print(f"Streamed: {safe_chunk}", end="", flush=True)
            full_output += safe_chunk
            
    # Flush remaining buffer
    for safe_chunk in sanitizer.flush():
        print(f"Streamed (Flush): {safe_chunk}", end="", flush=True)
        full_output += safe_chunk

    print("\n\n--- Final Output ---")
    print(full_output)

if __name__ == "__main__":
    main()

