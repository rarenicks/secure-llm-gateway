__version__ = "1.0.0"

from sentinel.factory import GuardrailsFactory
from sentinel.utils import download_spacy_model
from sentinel.streaming import StreamSanitizer
from sentinel.audit import BaseAuditLogger, FileAuditLogger, ConsoleAuditLogger, NullAuditLogger

# Optional integrations
try:
    from sentinel.integrations.langchain import SentinelRunnable
except ImportError:
    pass

try:
    from sentinel.integrations.llamaindex import SentinelNodePostprocessor
except ImportError:
    pass

try:
    from sentinel.integrations.openai import SentinelOpenAI, SentinelAsyncOpenAI
except ImportError:
    pass

try:
    from sentinel.integrations.huggingface import SentinelHFStreamer
except ImportError:
    pass
