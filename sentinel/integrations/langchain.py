from typing import Any, Dict, List, Optional
from sentinel.engine import GuardrailsEngine

try:
    from langchain_core.runnables import RunnableSerializable, RunnableConfig
    from langchain_core.messages import BaseMessage
    from langchain_core.pydantic_v1 import Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

if LANGCHAIN_AVAILABLE:
    class SentinelRunnable(RunnableSerializable[Any, Dict[str, Any]]):
        """
        LangChain Runnable integration for Semantic Sentinel.
        
        Usage:
            engine = GuardrailsFactory.load("finance")
            sentinel = SentinelRunnable(engine=engine)
            chain = prompt | sentinel | llm
        """
        engine: GuardrailsEngine = Field(..., description="The configured GuardrailsEngine")
        check_input: bool = Field(default=True, description="Whether to validate input")
        
        class Config:
            arbitrary_types_allowed = True

        def invoke(self, input: Any, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
            # Convert input to string
            text = self._to_string(input)
            
            # Validate
            result = self.engine.validate(text) if self.check_input else self.engine.validate_output(text)
            
            if not result.valid and result.action == "blocked":
                raise ValueError(f"Sentinel Blocked Request: {result.reason}")
                
            return {
                "sanitized_text": result.sanitized_text,
                "original_input": input,
                "metadata": {
                    "reason": result.reason,
                    "action": result.action
                }
            }
            
        def _to_string(self, input: Any) -> str:
            if isinstance(input, str):
                return input
            elif isinstance(input, dict):
                # Try common keys
                return input.get("content") or input.get("text") or str(input)
            elif isinstance(input, BaseMessage):
                return input.content
            return str(input)
else:
    # Dummy class if LangChain not installed
    class SentinelRunnable:
        def __init__(self, *args, **kwargs):
            raise ImportError("langchain-core not installed. Run `pip install langchain-core`")
