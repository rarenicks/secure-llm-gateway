from typing import Generator, List, Optional
import re
from sentinel.engine import GuardrailsEngine

class StreamSanitizer:
    """
    Helper class to sanitize streaming text (e.g. from LLM).
    It buffers text until a sentence boundary is detected, then runs
    the full GuardrailsEngine validation on that sentence.
    
    This ensures semantic blocking and context-aware PII redaction work
    even in streaming scenarios, at the cost of slight latency (one sentence).
    """
    
    # Simple sentence boundary detection (periods, questions, exclamations, newlines)
    # We look for punctuation followed by whitespace or end of string.
    SENTENCE_END = re.compile(r'(.*?[.?!])(\s+|$)', re.DOTALL)

    def __init__(self, engine: GuardrailsEngine):
        self.engine = engine
        self.buffer = ""

    def process(self, chunk: str) -> Generator[str, None, None]:
        """
        Ingests a text chunk and yields sanitized sentences if ready.
        """
        self.buffer += chunk
        
        while True:
            match = self.SENTENCE_END.match(self.buffer)
            if not match:
                break
                
            # We found a sentence!
            # group(1) is the sentence with punctuation
            # group(2) is the trailing whitespace
            sentence = match.group(1)
            separator = match.group(2)
            
            # Remove this from buffer
            # Calculate length correctly
            full_match_len = len(sentence) + len(separator)
            self.buffer = self.buffer[full_match_len:]
            
            # Validate
            result = self.engine.validate_output(sentence)
            
            if result.valid or result.action == "redacted":
                yield result.sanitized_text + separator
            else:
                # Blocked content is replaced or dropped
                yield f"[BLOCKED: {result.reason}]" + separator

    def flush(self) -> Generator[str, None, None]:
        """
        Process any remaining text in the buffer (e.g. at end of stream).
        """
        if self.buffer:
            result = self.engine.validate_output(self.buffer)
            self.buffer = ""
            if result.valid or result.action == "redacted":
                yield result.sanitized_text
            else:
                yield f"[BLOCKED: {result.reason}]"
