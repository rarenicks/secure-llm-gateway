import logging
import asyncio
from typing import List, Dict, Tuple, Optional
from functools import partial

logger = logging.getLogger("sentinel_presidio")

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False

class PresidioAdapter:
    """
    Enterprise PII Redaction using Microsoft Presidio.
    Requires: pip install presidio-analyzer presidio-anonymizer
    And model: python -m spacy download en_core_web_lg
    """
    def __init__(self, entities: Optional[List[str]] = None):
        self.enabled = PRESIDIO_AVAILABLE
        self.analyzer = None
        self.anonymizer = None
        
        if self.enabled:
            try:
                # Initialize engines (loads Spacy model)
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
                
                # Default entities if none provided
                # Presidio uses specific entity names: EMAIL_ADDRESS, PHONE_NUMBER, etc.
                self.entities = entities or [
                    "EMAIL_ADDRESS", 
                    "PHONE_NUMBER", 
                    "US_SSN", 
                    "CREDIT_CARD",
                    "IBAN_CODE",
                    "PERSON", # Optional: Redact names? Often aggressive.
                    "LOCATION" # Optional
                ]
                logger.info(f"Presidio Engine Loaded. Monitoring: {self.entities}")
            except Exception as e:
                logger.error(f"Failed to initialize Presidio (Model missing?): {e}")
                self.enabled = False
        else:
            logger.warning("Presidio libraries not found. Falling back to Regex PII.")

    def scan_and_redact(self, text: str) -> Tuple[str, List[str]]:
        """
        Returns (sanitized_text, list_of_detected_types)
        """
        if not self.enabled:
            return text, []

        try:
            # 1. Analyze
            results = self.analyzer.analyze(
                text=text,
                entities=self.entities,
                language='en'
            )
            
            if not results:
                return text, []

            # 2. Anonymize
            # We configure all detected entities to be replaced with <ENTITY_TYPE>
            operators = {}
            detected_types = set()
            
            for res in results:
                detected_types.add(res.entity_type)
                operators[res.entity_type] = OperatorConfig(
                    "replace", 
                    {"new_value": f"<{res.entity_type}_REDACTED>"}
                )

            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators=operators
            )
            
            return anonymized_result.text, [f"PII:{t}" for t in detected_types]

        except Exception as e:
            logger.error(f"Presidio Scan Failed: {e}")
            return text, []

    async def scan_and_redact_async(self, text: str) -> Tuple[str, List[str]]:
        """
        Async wrapper for scan_and_redact. Runs in a separate thread to avoid blocking.
        """
        if not self.enabled:
            return text, []
        
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.scan_and_redact, text)
