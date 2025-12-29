import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

class BaseAuditLogger(ABC):
    @abstractmethod
    def log(self, event: Dict[str, Any]):
        pass

class NullAuditLogger(BaseAuditLogger):
    def log(self, event: Dict[str, Any]):
        pass

class FileAuditLogger(BaseAuditLogger):
    """
    Logs audit events to a rotating JSONL file.
    Ideal for shipping logs to Splunk/Datadog via file agents.
    """
    def __init__(self, filepath: str = "sentinel_audit.jsonl"):
        self.filepath = filepath
        # Ensure directory exists
        path = Path(filepath)
        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: Dict[str, Any]):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **event
        }
        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            # Fallback to standard logging if file write fails
            logging.error(f"Failed to write audit log: {e}")

class ConsoleAuditLogger(BaseAuditLogger):
    def log(self, event: Dict[str, Any]):
        status = "ALLOWED" if event.get("valid") else "BLOCKED"
        if event.get("shadow_mode"):
            status += " (SHADOW)"
        
        print(f"[Sentinel Audit] {status} | Rule: {event.get('reason')} | Latency: {event.get('latency_ms'):.2f}ms")
