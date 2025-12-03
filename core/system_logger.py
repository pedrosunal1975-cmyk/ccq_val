"""
System Logger

Centralized logging system for CCQ Validator with structured output,
rotation, and context tracking.
"""

import logging
import json
import sys
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone  # Added timezone here
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from .config_loader import ConfigLoader


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging.
    
    Outputs logs in JSON format with consistent fields for
    machine-readable log aggregation and analysis.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add custom fields from extra parameter
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class SystemLogger:
    """
    Centralized logging system with support for both file and console output.
    
    Provides structured logging with automatic rotation, context tracking,
    and configurable output formats. Singleton pattern ensures consistent
    logging configuration across the application.
    """
    
    _instance: Optional['SystemLogger'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'SystemLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize system logger. Only runs once due to singleton pattern."""
        if SystemLogger._initialized:
            return
        
        self.config = ConfigLoader()
        self._setup_logging()
        SystemLogger._initialized = True
    
    def _setup_logging(self) -> None:
        """Configure logging system based on configuration."""
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        log_format = self.config.get('log_format', 'json')
        log_dir = self.config.get('log_dir')
        
        # Create log directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        if log_format == 'json':
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
        
        root_logger.addHandler(console_handler)
        
        # Add file handler with rotation
        log_file = log_dir / 'ccq_validator.log'
        
        rotation_type = self.config.get('log_rotation', 'daily')
        if rotation_type == 'daily':
            file_handler = TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=1,
                backupCount=self.config.get('log_retention_days', 30)
            )
        else:
            # Size-based rotation as fallback
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=self.config.get('log_retention_days', 30)
            )
        
        file_handler.setLevel(log_level)
        
        if log_format == 'json':
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
        
        root_logger.addHandler(file_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get logger instance for a specific module.
        
        Args:
            name: Logger name (typically __name__ of the module)
            
        Returns:
            Configured logger instance
        """
        return logging.getLogger(name)
    
    def log_with_context(
        self,
        logger: logging.Logger,
        level: int,
        message: str,
        **context: Any
    ) -> None:
        """
        Log message with additional context fields.
        
        Args:
            logger: Logger instance to use
            level: Log level (logging.INFO, logging.ERROR, etc.)
            message: Log message
            **context: Additional context fields to include in structured logs
        """
        extra = {'extra_fields': context}
        logger.log(level, message, extra=extra)


# Convenience function at module level (OUTSIDE the class)
def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return SystemLogger().get_logger(name)