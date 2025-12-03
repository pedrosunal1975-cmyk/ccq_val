"""
CCQ Mapper Logger - Main Orchestrator
======================================

Location: ccq_val/engines/ccq_mapper/reporting/mapper_logger.py

Enhanced structured logging specifically for CCQ's property-based mapper.
This module orchestrates specialized logging components

Features:
- Detailed phase tracking (load, extract, classify, cluster, construct, validate)
- Classification statistics logging
- Duplicate detection logging
- Gap analysis logging
- Success metrics logging
- Structured output with consistent formatting

Architecture: Designed for CCQ's unique workflow (property extraction → 
classification → clustering → construction → validation).

Components:
- logger_base: Core logger setup and configuration
- phase_logger: Phase tracking and timing
- classification_logger: Classification metrics
- duplicate_logger: Duplicate detection analysis
- quality_logger: Data quality assessment
- success_logger: Overall success metrics
- general_logger: General purpose logging

Usage:
    # Standard usage (backward compatible)
    from engines.ccq_mapper.reporting import get_mapper_logger
    
    logger = get_mapper_logger(filing_id="AAPL_10K_20231231")
    logger.log_phase_start("classify")
    logger.log_classification_summary(100, 95, 95.0)
    logger.log_success_summary(success_metrics)
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from core.system_logger import get_logger, SystemLogger
from .constants import (
    SECTION_SEPARATOR,
    SUBSECTION_SEPARATOR,
    MAX_DISPLAY_ITEMS,
    MAX_DISPLAY_DUPLICATES,
    MAX_DISPLAY_GAPS,
    LOG_LEVEL_MAPPING,
    TEMPLATE_PHASE_START,
    TEMPLATE_PHASE_COMPLETE,
    TEMPLATE_CLASSIFICATION_SUMMARY,
    TEMPLATE_CONFIDENCE_SUMMARY,
    TEMPLATE_DUPLICATE_SUMMARY,
    TEMPLATE_GAP_SUMMARY,
    TEMPLATE_SUCCESS_SUMMARY,
    SUCCESS_LEVEL_SYMBOLS,
    DUPLICATE_SEVERITY_LABELS
)

# Import specialized logger components
from .logger_base import MapperLoggerBase
from .phase_logger import PhaseLogger
from .classification_logger import ClassificationLogger
from .duplicate_logger import DuplicateLogger
from .quality_logger import QualityLogger
from .success_logger import SuccessLogger
from .general_logger import GeneralLogger


class MapperLogger:
    """
    Specialized logger for CCQ Mapper operations.
    
    Provides structured logging with mapper-specific context:
    - Filing identification
    - Processing phase tracking
    - Classification statistics
    - Quality metrics
    - Validation results
    
    Integrates with core.system_logger for consistent log format.
    
    This class orchestrates specialized logging components while
    maintaining full backward compatibility with existing code.
    """
    
    def __init__(self, filing_id: Optional[str] = None):
        """
        Initialize mapper logger.
        
        Args:
            filing_id: Optional filing ID for context
        """
        # Initialize base logger
        self.base = MapperLoggerBase(filing_id)
        
        # Initialize specialized logging components
        self.phase_logger = PhaseLogger(self.base)
        self.classification_logger = ClassificationLogger(self.base)
        self.duplicate_logger = DuplicateLogger(self.base)
        self.quality_logger = QualityLogger(self.base)
        self.success_logger = SuccessLogger(self.base)
        self.general_logger = GeneralLogger(self.base)
        
        # Expose base properties for backward compatibility
        self.system_logger = self.base.system_logger
        self.base_logger = self.base.base_logger
        self.filing_id = self.base.filing_id
    
    # ========================================================================
    # PHASE LOGGING (delegates to PhaseLogger)
    # ========================================================================
    
    def log_phase_start(self, phase: str, **context: Any):
        """
        Log start of a mapping phase.
        
        Args:
            phase: Phase name (load, extract, classify, cluster, construct, validate)
            **context: Additional context
        """
        self.phase_logger.log_phase_start(phase, **context)
    
    def log_phase_complete(self, phase: str, duration: float, **context: Any):
        """
        Log completion of a mapping phase.
        
        Args:
            phase: Phase name
            duration: Phase duration in seconds
            **context: Additional context
        """
        self.phase_logger.log_phase_complete(phase, duration, **context)
    
    # ========================================================================
    # CLASSIFICATION LOGGING (delegates to ClassificationLogger)
    # ========================================================================
    
    def log_classification_summary(
        self,
        total_facts: int,
        classified_facts: int,
        classification_rate: float,
        **context: Any
    ):
        """
        Log classification summary statistics.
        
        Args:
            total_facts: Total number of facts
            classified_facts: Number of successfully classified facts
            classification_rate: Classification success rate (percentage)
            **context: Additional context
        """
        self.classification_logger.log_classification_summary(
            total_facts,
            classified_facts,
            classification_rate,
            **context
        )
    
    def log_classification_distribution(
        self,
        distribution: Dict[str, Dict[str, int]]
    ):
        """
        Log classification distribution across dimensions.
        
        Args:
            distribution: Classification distribution dictionary
        """
        self.classification_logger.log_classification_distribution(
            distribution
        )
    
    def log_confidence_metrics(
        self,
        avg_confidence: float,
        high_count: int,
        medium_count: int,
        low_count: int
    ):
        """
        Log confidence metrics.
        
        Args:
            avg_confidence: Average confidence score
            high_count: Number of high-confidence classifications
            medium_count: Number of medium-confidence classifications
            low_count: Number of low-confidence classifications
        """
        self.classification_logger.log_confidence_metrics(
            avg_confidence,
            high_count,
            medium_count,
            low_count
        )
    
    def log_clustering_summary(
        self,
        cluster_count: int,
        clustered_facts: int,
        total_facts: int
    ):
        """
        Log clustering summary.
        
        Args:
            cluster_count: Number of clusters formed
            clustered_facts: Number of facts in clusters
            total_facts: Total number of facts
        """
        self.classification_logger.log_clustering_summary(
            cluster_count,
            clustered_facts,
            total_facts
        )
    
    # ========================================================================
    # CONSTRUCTION LOGGING (delegates to QualityLogger)
    # ========================================================================
    
    def log_statement_construction(
        self,
        statement_type: str,
        line_item_count: int
    ):
        """
        Log statement construction.
        
        Args:
            statement_type: Type of statement constructed
            line_item_count: Number of line items in statement
        """
        self.quality_logger.log_statement_construction(
            statement_type,
            line_item_count
        )
    
    # ========================================================================
    # DUPLICATE LOGGING (delegates to DuplicateLogger)
    # ========================================================================
    
    def log_duplicate_analysis(self, duplicate_report: Dict[str, Any]):
        """
        Log duplicate detection analysis.
        
        Args:
            duplicate_report: Duplicate analysis report
        """
        self.duplicate_logger.log_duplicate_analysis(duplicate_report)
    
    # Expose internal duplicate logging methods for backward compatibility
    def _log_duplicate_header(self, report: Dict[str, Any]):
        """Log duplicate analysis header."""
        self.duplicate_logger._log_duplicate_header(report)
    
    def _log_duplicate_severity_breakdown(self, report: Dict[str, Any]):
        """Log severity breakdown."""
        self.duplicate_logger._log_duplicate_severity_breakdown(report)
    
    def _log_duplicate_quality_assessment(self, report: Dict[str, Any]):
        """Log overall quality assessment."""
        self.duplicate_logger._log_duplicate_quality_assessment(report)
    
    def _log_critical_duplicate_details(self, report: Dict[str, Any]):
        """Log critical duplicate details."""
        self.duplicate_logger._log_critical_duplicate_details(report)
    
    def _log_major_duplicate_details(self, report: Dict[str, Any]):
        """Log major duplicate details."""
        self.duplicate_logger._log_major_duplicate_details(report)
    
    def _log_duplicate_footer(self):
        """Log duplicate analysis footer."""
        self.duplicate_logger._log_duplicate_footer()
    
    # ========================================================================
    # GAP ANALYSIS LOGGING (delegates to QualityLogger)
    # ========================================================================
    
    def log_gap_analysis(self, gap_report: Dict[str, Any]):
        """
        Log gap analysis results.
        
        Args:
            gap_report: Gap analysis report
        """
        self.quality_logger.log_gap_analysis(gap_report)
    
    # ========================================================================
    # NULL QUALITY LOGGING (delegates to QualityLogger)
    # ========================================================================
    
    def log_null_quality_summary(self, null_report: Dict[str, Any]):
        """
        Log null quality summary.
        
        Args:
            null_report: Null quality report
        """
        self.quality_logger.log_null_quality_summary(null_report)
    
    # ========================================================================
    # SUCCESS METRICS LOGGING (delegates to SuccessLogger)
    # ========================================================================
    
    def log_success_summary(self, success_metrics: Dict[str, Any]):
        """
        Log overall success summary.
        
        Args:
            success_metrics: Success metrics dictionary
        """
        self.success_logger.log_success_summary(success_metrics)
    
    # ========================================================================
    # ERROR LOGGING (delegates to GeneralLogger)
    # ========================================================================
    
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
        self.general_logger.log_error(error, phase, **context)
    
    def log_warning(self, message: str, **context: Any):
        """
        Log a warning.
        
        Args:
            message: Warning message
            **context: Additional context
        """
        self.general_logger.log_warning(message, **context)
    
    def log_info(self, message: str, **context: Any):
        """
        Log an info message.
        
        Args:
            message: Info message
            **context: Additional context
        """
        self.general_logger.log_info(message, **context)
    
    def log_debug(self, message: str, **context: Any):
        """
        Log a debug message.
        
        Args:
            message: Debug message
            **context: Additional context
        """
        self.general_logger.log_debug(message, **context)
    
    # ========================================================================
    # BACKWARD COMPATIBILITY METHODS
    # ========================================================================
    
    def _setup_mapper_log(self):
        """Setup mapper log (backward compatibility - now handled in base)."""
        pass  # Already handled in MapperLoggerBase.__init__
    
    def _add_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add filing context (backward compatibility)."""
        return self.base._add_context(context)


def get_mapper_logger(filing_id: Optional[str] = None) -> MapperLogger:
    """
    Get mapper logger instance.
    
    Args:
        filing_id: Optional filing ID for context
        
    Returns:
        MapperLogger instance
    """
    return MapperLogger(filing_id=filing_id)


__all__ = ['MapperLogger', 'get_mapper_logger']