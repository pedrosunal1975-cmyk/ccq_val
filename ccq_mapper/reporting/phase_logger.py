"""
Phase Logger
============

Location: ccq_val/engines/ccq_mapper/reporting/phase_logger.py

Logging for mapping phase tracking.

Functions:
- log_phase_start: Log start of a mapping phase
- log_phase_complete: Log completion of a mapping phase
- log_phase_error: Log phase-specific errors

Phases tracked:
- load: Loading XBRL data
- extract: Extracting properties
- classify: Classifying facts
- cluster: Clustering related facts
- construct: Constructing statements
- validate: Validating output
"""

import logging
from typing import Any

from .constants import TEMPLATE_PHASE_START, TEMPLATE_PHASE_COMPLETE
from .logger_base import MapperLoggerBase


class PhaseLogger:
    """Handles logging for mapping phases."""
    
    def __init__(self, base_logger: MapperLoggerBase):
        """
        Initialize phase logger.
        
        Args:
            base_logger: MapperLoggerBase instance
        """
        self.base = base_logger
    
    def log_phase_start(self, phase: str, **context: Any):
        """
        Log start of a mapping phase.
        
        Args:
            phase: Phase name (load, extract, classify, cluster, construct, validate)
            **context: Additional context
        """
        message = TEMPLATE_PHASE_START.format(phase=phase)
        
        full_context = self.base._add_context({
            'phase': phase,
            'event': 'phase_start',
            **context
        })
        
        self.base.system_logger.log_with_context(
            self.base.base_logger,
            logging.INFO,
            message,
            **full_context
        )
    
    def log_phase_complete(
        self,
        phase: str,
        duration: float,
        **context: Any
    ):
        """
        Log completion of a mapping phase.
        
        Args:
            phase: Phase name
            duration: Phase duration in seconds
            **context: Additional context
        """
        message = TEMPLATE_PHASE_COMPLETE.format(
            phase=phase,
            duration=duration
        )
        
        full_context = self.base._add_context({
            'phase': phase,
            'event': 'phase_complete',
            'duration_seconds': duration,
            **context
        })
        
        self.base.system_logger.log_with_context(
            self.base.base_logger,
            logging.INFO,
            message,
            **full_context
        )
    
    def log_phase_error(
        self,
        phase: str,
        error: Exception,
        **context: Any
    ):
        """
        Log error during a mapping phase.
        
        Args:
            phase: Phase name where error occurred
            error: Exception that was raised
            **context: Additional context
        """
        message = f"Error in phase '{phase}': {str(error)}"
        
        full_context = self.base._add_context({
            'phase': phase,
            'event': 'phase_error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            **context
        })
        
        self.base.system_logger.log_with_context(
            self.base.base_logger,
            logging.ERROR,
            message,
            **full_context
        )