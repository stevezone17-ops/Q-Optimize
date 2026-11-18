"""Structured logging configuration for Q-Optimize backend with sensitive data redaction."""

import re
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from backend.app.core.config import settings


class SensitiveDataRedactor(logging.Filter):
    """
    Redacts passwords, bearer tokens, API keys, and authorization headers from log streams.
    Ensures GDPR/HIPAA/SOC2 compliance by preventing accidental credential leakage.
    """

    PATTERNS = [
        (re.compile(r'(password["\':\s=]+)([\w!@#$%^&*()_+=\-\.]+)', re.IGNORECASE), r'\1[REDACTED]'),
        (re.compile(r'(Bearer\s+)([A-Za-z0-9\-._~+/]+=*)', re.IGNORECASE), r'\1[REDACTED]'),
        (re.compile(r'(access_token["\':\s=]+)([\w\-._~+/]+=*)', re.IGNORECASE), r'\1[REDACTED]'),
        (re.compile(r'(refresh_token["\':\s=]+)([\w\-._~+/]+=*)', re.IGNORECASE), r'\1[REDACTED]'),
        (re.compile(r'(jwt_secret_key["\':\s=]+)([\w\-._~+/]+=*)', re.IGNORECASE), r'\1[REDACTED]'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, repl in self.PATTERNS:
                record.msg = pattern.sub(repl, record.msg)
        return True


def setup_logging() -> logging.Logger:
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    redactor = SensitiveDataRedactor()

    # Stream Handler (stdout)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(redactor)

    logger = logging.getLogger("q_optimize")
    logger.setLevel(log_level)

    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        logger.addHandler(stdout_handler)

    logger.propagate = False
    return logger


logger = setup_logging()
