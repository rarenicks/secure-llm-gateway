import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Configure application logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audit_logger")

DB_FILE = "audit.db"

def init_db():
    """Initializes the SQLite database for audit logging."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            client_ip TEXT,
            original_prompt TEXT,
            sanitized_prompt TEXT,
            verdict TEXT,
            latency REAL,
            metadata TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"Audit database initialized at {DB_FILE}")

def log_request(
    client_ip: str,
    original_prompt: str,
    sanitized_prompt: str,
    verdict: str,
    latency: float,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Logs a request to the SQLite database.
    Designed to be run as a BackgroundTask to avoid blocking the API response.
    """
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = conn.cursor()
        
        timestamp = datetime.utcnow().isoformat()
        metadata_json = json.dumps(metadata) if metadata else "{}"
        
        cursor.execute("""
            INSERT INTO audit_logs (timestamp, client_ip, original_prompt, sanitized_prompt, verdict, latency, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, client_ip, original_prompt, sanitized_prompt, verdict, latency, metadata_json))
        
        conn.commit()
        conn.close()
        logger.info(f"Logged request from {client_ip} - Verdict: {verdict}")
    except Exception as e:
        logger.error(f"Failed to write to audit log: {e}")
