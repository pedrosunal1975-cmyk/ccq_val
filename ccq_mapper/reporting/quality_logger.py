"""
Quality Logger
==============

Location: ccq_val/engines/ccq_mapper/reporting/quality_logger.py

Logging for data quality analysis.

Functions:
- log_gap_analysis: Classification gap analysis
- log_null_quality_summary: Null value quality assessment
- log_statement_construction: Statement construction results

Features:
- Gap pattern detection
- Null quality scoring
- Statement completeness tracking
"""

import logging
from typing import Any, Dict

from .constants import SECTION_SEPARATOR
from .logger_base import MapperLoggerBase


class QualityLogger:
    """Handles logging for data quality analysis."""
    
    def __init__(self, base_logger: MapperLoggerBase):
        """
        Initialize quality logger.
        
        Args:
            base_logger: MapperLoggerBase instance
        """
        self.base = base_logger
    
    def log_gap_analysis(self, gap_report: Dict[str, Any]):
        """
        Log gap analysis results.
        
        Args:
            gap_report: Gap analysis report dictionary
        """
        gap_count = gap_report.get('gap_count', 0)
        
        if gap_count == 0:
            self.base.base_logger.info(
                "\n[OK] No classification gaps detected\n"
            )
            return
        
        gap_percentage = gap_report.get('gap_percentage', 0.0)
        
        self.base.base_logger.warning(f"\n{SECTION_SEPARATOR}")
        self.base.base_logger.warning("CLASSIFICATION GAP ANALYSIS")
        self.base.base_logger.warning(SECTION_SEPARATOR)
        self.base.base_logger.warning(
            f"Total classification gaps: {gap_count} "
            f"({gap_percentage:.1f}%)"
        )
        
        # Log gap patterns
        patterns = gap_report.get('patterns', {})
        gap_type_counts = patterns.get('gap_type_counts', {})
        
        if gap_type_counts:
            self.base.base_logger.warning("\nGap Types:")
            for gap_type, count in gap_type_counts.items():
                self.base.base_logger.warning(f"  - {gap_type}: {count}")
        
        # Log recommendations
        recommendations = gap_report.get('recommendations', [])
        if recommendations:
            self.base.base_logger.warning("\nRecommendations:")
            for rec in recommendations[:5]:  # Top 5 recommendations
                self.base.base_logger.warning(f"  {rec}")
        
        self.base.base_logger.warning(f"{SECTION_SEPARATOR}\n")
    
    def log_null_quality_summary(self, null_report: Dict[str, Any]):
        """
        Log null quality summary.
        
        Args:
            null_report: Null quality report dictionary
        """
        score = null_report.get('quality_score', {}).get('score', 0.0)
        grade = null_report.get('quality_score', {}).get('grade', 'UNKNOWN')
        
        self.base.base_logger.info(f"\n{SECTION_SEPARATOR}")
        self.base.base_logger.info("NULL QUALITY SUMMARY")
        self.base.base_logger.info(SECTION_SEPARATOR)
        self.base.base_logger.info(f"Quality Score: {score:.1f}/100 ({grade})")
        
        summary = null_report.get('summary', {})
        total_nulls = summary.get('total_nulls', 0)
        
        if total_nulls > 0:
            self.base.base_logger.info(f"Total nulls: {total_nulls}")
            self.base.base_logger.info(
                f"  - Legitimate: {summary.get('legitimate_nils', 0)}"
            )
            self.base.base_logger.info(
                f"  - Expected: {summary.get('expected_nulls', 0)}"
            )
            self.base.base_logger.info(
                f"  - Anomalous: {summary.get('anomalous_nulls', 0)}"
            )
        else:
            self.base.base_logger.info("[OK] No null values detected")
        
        self.base.base_logger.info(f"{SECTION_SEPARATOR}\n")
    
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
        message = (
            f"Constructed {statement_type}: {line_item_count} line items"
        )
        
        full_context = self.base._add_context({
            'event': 'statement_constructed',
            'statement_type': statement_type,
            'line_item_count': line_item_count
        })
        
        self.base.system_logger.log_with_context(
            self.base.base_logger,
            logging.INFO,
            message,
            **full_context
        )