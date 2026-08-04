"""
Structured logging module for VideoAgent with sensitive credential redaction filters.
Conforms to Production Requirement #8.
"""
import logging
import re
import sys
from typing import Any

# Patterns matching sensitive fields to redact
SENSITIVE_PATTERNS = [
    (re.compile(r'rtsp://([^:]+):([^@]+)@', re.IGNORECASE), r'rtsp://\1:***REDACTED***@'),
    (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'\s&]+)["\']?', re.IGNORECASE), r'password="***REDACTED***"'),
    (re.compile(r'client_secret["\']?\s*[:=]\s*["\']?([^"\'\s&]+)["\']?', re.IGNORECASE), r'client_secret="***REDACTED***"'),
    (re.compile(r'access_token["\']?\s*[:=]\s*["\']?([^"\'\s&]+)["\']?', re.IGNORECASE), r'access_token="***REDACTED***"'),
    (re.compile(r'Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*', re.IGNORECASE), r'Bearer ***REDACTED***'),
]

class SensitiveDataRedactor(logging.Filter):
    """Logging filter that scrubs sensitive passwords and tokens from log records."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: (self.redact(str(v)) if isinstance(v, str) else v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.redact(str(arg)) if isinstance(arg, str) else arg for arg in record.args)
        return True

    @staticmethod
    def redact(text: str) -> str:
        if not text:
            return text
        sanitized = text
        for pattern, replacement in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized

def setup_structured_logging(level: int = logging.INFO):
    """Configures structured console logging with credential redaction."""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove existing handlers
    for h in logger.handlers[:]:
        logger.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataRedactor())
    logger.addHandler(handler)

    return logger

logger = logging.getLogger("vms_system")
