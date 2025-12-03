"""
General Purpose Logger
======================

Location: ccq_val/engines/ccq_mapper/reporting/general_logger.py

General purpose logging functions.

Functions:
- log_error: Log errors with context
- log_warning: Log warnings
- log_info: Log informational messages
- log_debug: Log debug messages

Features:
- Consistent error logging with traceback
- Context-aware logging
- Multiple log levels
"""

import logging
from typing import Any, Optional

from .logger_base import MapperLoggerBase


class GeneralLogger:
    """Handles general purpose logging operations."""
    
    def __init__(self, base_logger: MapperLoggerBase):
        """
        Initialize general logger.
        
        Args:
            base_logger: MapperLoggerBase instance
        """
        self.base = base_logger
    
    def log_error(
        self,
        error: Exception,
        phase: Optional[str] = None,
        **context: Any
    ):
        """
        Log an error during mapping.
        
        Args:
            error: Exception that occurred
            phase: Phase where error occurred (optional)
            **context: Additional context
        """
        full_context = self.base._add_context({
            'event': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'phase': phase,
            **context
        })
        
        self.base.system_logger.log_with_context(
            self.base.base_logger,
            logging.ERROR,
            f"Error in {phase or 'mapping'}: {str(error)}",
            **full_context
        )
        
        self.base.base_logger.exception("Full traceback:")
    
    def log_warning(self, message: str, **context: Any):
        """
        Log a warning.
        
        Args:
            message: Warning message
            **context: Additional context
        """
        full_context = self.base._add_context({
            'event': 'warning',
            **context
        })
        
        self.base.system_logger.log_with_context(
            self.base.base_logger,
            logging.WARNING,
            message,
            **full_context
        )
    
    def log_info(self, message: str, **context: Any):
        """
        Log an info message.
        
        Args:
            message: Info message
            **context: Additional context
        """
        full_context = self.base._add_context({
            'event': 'info',
            **context
        })
        
        self.base.system_logger.log_with_context(
            self.base.base_logger,
            logging.INFO,
            message,
            **full_context
        )
    
    def log_debug(self, message: str, **context: Any):
        """
        Log a debug message.
        
        Args:
            message: Debug message
            **context: Additional context
        """
        full_context = self.base._add_context({
            'event': 'debug',
            **context
        })
        
        self.base.system_logger.log_with_context(
            self.base.base_logger,
            logging.DEBUG,
            message,
            **full_context
        )