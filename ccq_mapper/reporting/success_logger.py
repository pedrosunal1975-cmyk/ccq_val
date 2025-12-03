"""
Success Metrics Logger
======================

Location: ccq_val/engines/ccq_mapper/reporting/success_logger.py

Logging for overall mapping success metrics.

Functions:
- log_success_summary: Overall success metrics and recommendations

Features:
- Overall success scoring
- Key metrics summary
- Actionable recommendations
- Success level classification
"""

import logging
from typing import Any, Dict

from .constants import (
    SECTION_SEPARATOR,
    TEMPLATE_SUCCESS_SUMMARY,
    SUCCESS_LEVEL_SYMBOLS
)
from .logger_base import MapperLoggerBase


class SuccessLogger:
    """Handles logging for overall mapping success metrics."""
    
    def __init__(self, base_logger: MapperLoggerBase):
        """
        Initialize success logger.
        
        Args:
            base_logger: MapperLoggerBase instance
        """
        self.base = base_logger
    
    def log_success_summary(self, success_metrics: Dict[str, Any]):
        """
        Log overall success summary.
        
        Args:
            success_metrics: Success metrics dictionary
        """
        overall_score = success_metrics.get('overall_score', 0.0)
        success_level = success_metrics.get('success_level', 'UNKNOWN')
        symbol = SUCCESS_LEVEL_SYMBOLS.get(success_level, '?')
        
        message = TEMPLATE_SUCCESS_SUMMARY.format(
            score=overall_score,
            level=success_level
        )
        
        self.base.base_logger.info(f"\n{SECTION_SEPARATOR}")
        self.base.base_logger.info(f"MAPPING SUCCESS SUMMARY {symbol}")
        self.base.base_logger.info(SECTION_SEPARATOR)
        self.base.base_logger.info(message)
        
        # Log key metrics
        self._log_key_metrics(success_metrics)
        
        # Log recommendations
        self._log_recommendations(success_metrics)
        
        self.base.base_logger.info(f"{SECTION_SEPARATOR}\n")
    
    def _log_key_metrics(self, success_metrics: Dict[str, Any]):
        """
        Log key metrics from success summary.
        
        Args:
            success_metrics: Success metrics dictionary
        """
        # Classification metrics
        classification = success_metrics.get('classification_success', {})
        classification_rate = classification.get('classification_rate', 0.0)
        self.base.base_logger.info(
            f"\nClassification: {classification_rate:.1f}% complete"
        )
        
        # Confidence metrics
        confidence = success_metrics.get('confidence_metrics', {})
        avg_confidence = confidence.get('average_confidence', 0.0)
        self.base.base_logger.info(
            f"Confidence: Avg {avg_confidence:.2f}"
        )
        
        # Statement metrics
        statements = success_metrics.get('statement_success', {})
        statement_count = statements.get('statement_count', 0)
        self.base.base_logger.info(
            f"Statements: {statement_count} constructed"
        )
        
        # Null quality metrics
        null_quality = success_metrics.get('null_quality_score', 0.0)
        self.base.base_logger.info(
            f"Null Quality: {null_quality:.1f}/100"
        )
    
    def _log_recommendations(self, success_metrics: Dict[str, Any]):
        """
        Log recommendations from success summary.
        
        Args:
            success_metrics: Success metrics dictionary
        """
        recommendations = success_metrics.get('recommendations', [])
        
        if not recommendations:
            return
        
        self.base.base_logger.info("\nKey Recommendations:")
        
        for rec in recommendations[:5]:  # Top 5
            # Determine log level based on recommendation content
            if '[ERROR]' in rec:
                level = logging.ERROR
            elif '[WARNING]' in rec:
                level = logging.WARNING
            else:
                level = logging.INFO
            
            self.base.base_logger.log(level, f"  {rec}")