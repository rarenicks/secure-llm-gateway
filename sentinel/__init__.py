__version__ = "0.1.0"

from sentinel.factory import GuardrailsFactory
from sentinel.utils import download_spacy_model
from sentinel.streaming import StreamSanitizer
# Optional integrations
try:
    from sentinel.integrations.langchain import SentinelRunnable
except ImportError:
    pass
