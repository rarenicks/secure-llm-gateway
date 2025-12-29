from typing import Optional
from sentinel.engine import GuardrailsEngine
from sentinel.streaming import StreamSanitizer

try:
    from transformers import TextIteratorStreamer, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

if TRANSFORMERS_AVAILABLE:
    class SentinelHFStreamer(TextIteratorStreamer):
        """
        HuggingFace Streamer with built-in Guardrails.
        
        Usage:
            tokenizer = AutoTokenizer.from_pretrained(...)
            engine = GuardrailsFactory.load("finance")
            streamer = SentinelHFStreamer(tokenizer, engine)
            
            model.generate(..., streamer=streamer)
            
            for token in streamer:
                print(token, end="")
        """
        def __init__(self, tokenizer: "AutoTokenizer", engine: GuardrailsEngine, **kwargs):
            super().__init__(tokenizer, **kwargs)
            self.engine = engine
            self.sanitizer = StreamSanitizer(self.engine)
            # Internal buffer for sanitized chunks
            self._sanitized_queue = []

        def put(self, value):
            """
            Receives tokens from model.generate(), decodes them, sanitizes, and queues them.
            """
            # Allow the parent to handle decoding logic (keeping text in self.text_queue)
            super().put(value)

        def __next__(self):
            # 1. If we have sanitized chunks ready, yield them
            if self._sanitized_queue:
                return self._sanitized_queue.pop(0)

            # 2. Get next text chunk from parent (TextIteratorStreamer yields decoded strings)
            try:
                text_chunk = super().__next__()
            except StopIteration:
                # Flush the sanitizer
                for safe_chunk in self.sanitizer.flush():
                    self._sanitized_queue.append(safe_chunk)
                
                if self._sanitized_queue:
                    return self._sanitized_queue.pop(0)
                raise StopIteration

            # 3. Process chunk through sanitizer
            for safe_chunk in self.sanitizer.process(text_chunk):
                self._sanitized_queue.append(safe_chunk)
            
            # 4. If we produced sanitized output, yield it. 
            # If not (buffered inside sanitizer), recurse to get next chunk.
            if self._sanitized_queue:
                return self._sanitized_queue.pop(0)
            else:
                # Recurse until we get output or StopIteration
                return self.__next__()

else:
    class SentinelHFStreamer:
        def __init__(self, *args, **kwargs):
            raise ImportError("transformers not installed. Run `pip install transformers`")
