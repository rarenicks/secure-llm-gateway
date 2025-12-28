import pytest
from unittest.mock import MagicMock, patch
from sentinel.engine import GuardrailsEngine

def test_presidio_initialization_failure_fallback():
    # Simulate Presidio NOT being available
    with patch("sentinel.presidio_adapter.PRESIDIO_AVAILABLE", False):
        config = {
            "detectors": {
                "pii": {
                    "enabled": True,
                    "engine": "presidio", # User REQUESTED Presidio
                    "patterns": ["EMAIL"]
                }
            }
        }
        engine = GuardrailsEngine(config)
        
        # Should have fallen back to regex
        assert engine.pii_engine_type == "regex"
        assert len(engine.pii_patterns) > 0
        assert engine.presidio is not None
        assert engine.presidio.enabled is False

def test_presidio_initialization_success():
    # We must simulate that the modules exist BEFORE the adapter is imported or re-imported.
    # Since it's already imported, we might need to reload it or just patch the class attributes directly.
    # However, proper way to mock missing imports is patching sys.modules.
    
    mock_analyzer_cls = MagicMock()
    mock_anonymizer_cls = MagicMock()
    
    # Mock the modules
    modules = {
        "presidio_analyzer": MagicMock(AnalyzerEngine=mock_analyzer_cls),
        "presidio_anonymizer": MagicMock(AnonymizerEngine=mock_anonymizer_cls),
        "presidio_anonymizer.entities": MagicMock()
    }
    
    with patch.dict("sys.modules", modules):
        # We need to reload the module so it tries the imports again
        import importlib
        import sentinel.presidio_adapter
        importlib.reload(sentinel.presidio_adapter)
        
        # Now we can patch the adapter's internal classes if needed, 
        # or just rely on the reloaded module finding our mocks.
        
        config = {
            "detectors": {
                "pii": {
                    "enabled": True,
                    "engine": "presidio"
                }
            }
        }
        
        # We also need to reload engine to pick up the reloaded adapter class?
        # Or just instantiate the adapter manually to test it?
        # Let's test the Engine integration.
        import sentinel.engine
        importlib.reload(sentinel.engine)
        
        engine = sentinel.engine.GuardrailsEngine(config)
        
        assert engine.pii_engine_type == "presidio"
        assert engine.presidio.enabled is True
        
        # Verify our mock classes were instantiated
        # (The reloaded module used our sys.modules mocks)
        mock_analyzer_cls.assert_called()
        mock_anonymizer_cls.assert_called()
        
        # Restore module state (best effort)
        importlib.reload(sentinel.presidio_adapter)

