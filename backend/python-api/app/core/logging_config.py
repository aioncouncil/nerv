"""
Logging configuration for the NERV Geometry Engine API.

Uses structured logging with structlog for better observability
and debugging capabilities.
"""

import logging
import logging.config
import sys
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory

from app.core.config import get_settings

settings = get_settings()


def setup_logging():
    """Configure structured logging for the application."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )
    
    # Configure structlog
    if settings.log_format == "json":
        # JSON logging for production
        structlog.configure(
            processors=[
                # Add standard fields to every log entry
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                # Add timestamp
                structlog.processors.TimeStamper(fmt="iso"),
                # JSON output
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        # Human-readable logging for development
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                # Add timestamp
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                # Colorized console output
                structlog.dev.ConsoleRenderer(colors=True)
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


def get_logger(name: str = "nerv"):
    """Get a configured logger instance."""
    return structlog.get_logger(name)


# Logging configuration dict for uvicorn
LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=True) 
            if settings.log_format != "json" 
            else structlog.processors.JSONRenderer(),
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": settings.log_level,
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["default"],
            "level": "INFO", 
            "propagate": False,
        },
        "fastapi": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        "nerv": {
            "handlers": ["default"],
            "level": settings.log_level,
            "propagate": False,
        },
    },
}