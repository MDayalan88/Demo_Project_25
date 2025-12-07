"""
Logging utility for FileFerry Agent
Provides structured JSON logging with AWS integration
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    Compatible with AWS CloudWatch Logs Insights
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),  # ✅ Fixed deprecation warning
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'transfer_id'):
            log_data["transfer_id"] = record.transfer_id
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        
        return json.dumps(log_data)


def get_logger(
    name: str,
    level: str = "INFO",
    format_type: str = "json"
) -> logging.Logger:
    """
    Get or create a logger instance
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ('json' or 'text')
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("FileFerry agent started")
        >>> logger.error("Transfer failed", extra={"transfer_id": "123"})
    """
    
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Set formatter
    if format_type == "json":
        formatter = JSONFormatter()
    else:
        # Text format for local development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Don't propagate to root logger
    logger.propagate = False
    
    return logger


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log message with additional context
    
    Args:
        logger: Logger instance
        level: Log level (info, warning, error, etc.)
        message: Log message
        context: Additional context dictionary
    
    Example:
        >>> logger = get_logger(__name__)
        >>> log_with_context(
        ...     logger, 
        ...     "info",
        ...     "Transfer started",
        ...     {"user_id": "user@example.com", "transfer_id": "123"}
        ... )
    """
    
    log_func = getattr(logger, level.lower())
    
    if context:
        log_func(message, extra=context)
    else:
        log_func(message)


# Pre-configured logger for the FileFerry agent
fileferry_logger = get_logger(
    "fileferry",
    level="INFO",
    format_type="json"
)


# Convenience functions
def info(message: str, **context):
    """Log info message with context"""
    log_with_context(fileferry_logger, "info", message, context)


def warning(message: str, **context):
    """Log warning message with context"""
    log_with_context(fileferry_logger, "warning", message, context)


def error(message: str, **context):
    """Log error message with context"""
    log_with_context(fileferry_logger, "error", message, context)


def debug(message: str, **context):
    """Log debug message with context"""
    log_with_context(fileferry_logger, "debug", message, context)


# Example usage for testing
if __name__ == "__main__":
    # Test JSON logging
    logger = get_logger("test", format_type="json")
    
    logger.info("FileFerry agent initialized")
    logger.warning("High memory usage detected")
    logger.error("Transfer failed", extra={
        "transfer_id": "transfer-123",
        "user_id": "user@example.com",
        "error_code": "SFTP_CONNECTION_FAILED"
    })
    
    try:
        raise ValueError("Test exception")
    except Exception:
        logger.exception("Exception occurred")
    
    print("\n" + "="*70)
    print("✅ Logger test complete")
    print("="*70)