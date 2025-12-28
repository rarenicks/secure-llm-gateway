import pytest
from sentinel.engine import GuardrailsEngine

# Mock config for testing
@pytest.fixture
def basic_config():
    return {
        "profile_name": "TestProfile",
        "detectors": {
            "pii": {
                "enabled": True,
                "patterns": ["EMAIL"]
            },
            "topics": {
                "enabled": True,
                "block_list": ["forbidden"]
            },
            "semantic_blocking": {
                "enabled": False # Disable for unit tests to avoid loading model
            }
        }
    }

def test_pii_redaction(basic_config):
    engine = GuardrailsEngine(basic_config)
    text = "My email is test@example.com"
    result = engine.validate(text)
    
    assert result.valid is True # PII is redacted, so it's "valid" but changed
    assert result.action == "redacted"
    assert "<EMAIL_REDACTED>" in result.sanitized_text
    assert "test@example.com" not in result.sanitized_text

def test_topic_blocking(basic_config):
    engine = GuardrailsEngine(basic_config)
    text = "This text contains forbidden content."
    result = engine.validate(text)
    
    assert result.valid is False
    assert result.action == "blocked"
    assert "Topic:forbidden" in result.reason

def test_clean_text(basic_config):
    engine = GuardrailsEngine(basic_config)
    text = "This is clean text."
    result = engine.validate(text)
    
    assert result.valid is True
    assert result.action == "allowed"
    assert result.sanitized_text == text
