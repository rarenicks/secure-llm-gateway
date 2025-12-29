"""
Test LangChain Integration for Semantic Sentinel
"""
from sentinel.factory import GuardrailsFactory

try:
    from sentinel.integrations.langchain import SentinelRunnable
    from langchain_core.prompts import PromptTemplate
    from langchain_core.runnables import RunnableLambda
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("LangChain not installed. Skipping integration test.")
    print("Install with: pip install langchain-core")

def mock_llm(input_dict):
    """Mock LLM that just echoes back the sanitized text"""
    return f"LLM Response: {input_dict['sanitized_text']}"

def main():
    if not LANGCHAIN_AVAILABLE:
        return
        
    print("Initializing Sentinel...")
    engine = GuardrailsFactory.load("finance")
    sentinel = SentinelRunnable(engine=engine, check_input=True)
    
    # Create a simple chain: sentinel -> mock_llm
    llm_runnable = RunnableLambda(mock_llm)
    chain = sentinel | llm_runnable
    
    print("\n--- Test 1: Safe Input ---")
    try:
        result = chain.invoke("What is 2+2?")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n--- Test 2: PII Input (Should Redact) ---")
    try:
        result = chain.invoke("My phone is 555-123-4567")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n--- Test 3: Blocked Input (Should Raise ValueError) ---")
    try:
        result = chain.invoke("How do I commit insider trading?")
        print(f"Result: {result}")
    except ValueError as e:
        print(f"✅ Correctly blocked: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    print("\n✅ LangChain Integration Test Complete!")

if __name__ == "__main__":
    main()
