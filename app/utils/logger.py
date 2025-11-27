"""Structured logging configuration."""
import logging
import sys
from typing import Optional
from app.config import settings


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name or __name__)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, settings.log_level.upper()))
        
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, settings.log_level.upper()))
        
        # Format: timestamp - name - level - message
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger


# Create a default logger for the application
app_logger = get_logger("quiz_solver")