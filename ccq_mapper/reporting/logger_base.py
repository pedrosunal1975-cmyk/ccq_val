"""
Mapper Logger Base
==================

Location: ccq_val/engines/ccq_mapper/reporting/logger_base.py

Base logger setup and configuration for CCQ Mapper.

Classes:
- MapperLoggerBase: Base logger with core functionality

Features:
- Filing context management
- Structured logging integration
- Log file setup and rotation
"""

import logging
from typing import Any, Dict, Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler

from core.system_logger import get_logger, SystemLogger


class MapperLoggerBase:
    """
    Base logger for CCQ Mapper operations.
    
    Provides core logging functionality with filing context
    and structured logging integration.
    """
    
    def __init__(self, filing_id: Optional[str] = None):
        """
        Initialize base mapper logger.
        
        Args:
            filing_id: Optional filing ID for context
        """
        self.system_logger = SystemLogger()
        self.base_logger = get_logger('ccq_mapper')
        self.filing_id = filing_id
        
        # Setup mapper-specific log file
        self._setup_mapper_log()
    
    def _setup_mapper_log(self):
        """Set up mapper-specific log file with rotation."""
        config = self.system_logger.config
        log_dir = config.get('mapper_logs_path')
        
        if not log_dir:
            return
        
        # Create log directory
        mapper_log_dir = Path(log_dir)
        mapper_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup rotating file handler
        mapper_log_file = mapper_log_dir / 'ccq_mapper.log'
        file_handler = RotatingFileHandler(
            mapper_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        
        # Setup formatter
        log_format = config.get('log_format', 'json')
        if log_format == 'json':
            from core.system_logger import StructuredFormatter
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        self.base_logger.addHandler(file_handler)
    
    def _add_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add filing context to log entry.
        
        Args:
            context: Additional context dictionary
            
        Returns:
            Full context with filing ID if available
        """
        full_context = {}
        if self.filing_id:
            full_context['filing_id'] = self.filing_id
        full_context.update(context)
        return full_context
    
    def log_with_level(
        self,
        level: int,
        message: str,
        **context: Any
    ):
        """
        Log message with specified level.
        
        Args:
            level: Logging level (INFO, WARNING, ERROR, etc.)
            message: Log message
            **context: Additional context
        """
        full_context = self._add_context(context)
        
        self.system_logger.log_with_context(
            self.base_logger,
            level,
            message,
            **full_context
        )