"""
Duplicate Logger
================

Location: ccq_val/engines/ccq_mapper/reporting/duplicate_logger.py

Logging for duplicate detection analysis.

Functions:
- log_duplicate_analysis: Main duplicate analysis logging
- _log_duplicate_header: Header with summary statistics
- _log_duplicate_severity_breakdown: Severity classification
- _log_duplicate_quality_assessment: Quality impact assessment
- _log_critical_duplicate_details: Critical duplicate findings
- _log_major_duplicate_details: Major duplicate findings

Severity Levels:
- CRITICAL: >5% variance - severe data issues
- MAJOR: 1-5% variance - review recommended
- MINOR: <1% variance - low impact
- REDUNDANT: Exact match - no impact
"""

import logging
from typing import Any, Dict

from .constants import (
    SECTION_SEPARATOR,
    MAX_DISPLAY_DUPLICATES,
    DUPLICATE_SEVERITY_LABELS
)
from .logger_base import MapperLoggerBase


class DuplicateLogger:
    """Handles logging for duplicate detection analysis."""
    
    def __init__(self, base_logger: MapperLoggerBase):
        """
        Initialize duplicate logger.
        
        Args:
            base_logger: MapperLoggerBase instance
        """
        self.base = base_logger
    
    def log_duplicate_analysis(self, duplicate_report: Dict[str, Any]):
        """
        Log duplicate detection analysis.
        
        Args:
            duplicate_report: Duplicate analysis report dictionary
        """
        total_groups = duplicate_report.get('total_duplicate_groups', 0)
        
        if total_groups == 0:
            self._log_clean_filing()
            return
        
        # Log duplicate findings
        self._log_duplicate_header(duplicate_report)
        self._log_duplicate_severity_breakdown(duplicate_report)
        self._log_duplicate_quality_assessment(duplicate_report)
        self._log_critical_duplicate_details(duplicate_report)
        self._log_major_duplicate_details(duplicate_report)
        self._log_duplicate_footer()
    
    def _log_clean_filing(self):
        """Log message for clean filing with no duplicates."""
        self.base.base_logger.info(f"\n{SECTION_SEPARATOR}")
        self.base.base_logger.info("DUPLICATE DETECTION - CLEAN XBRL FILING")
        self.base.base_logger.info(SECTION_SEPARATOR)
        self.base.base_logger.info(
            "[OK] No duplicate facts detected in source XBRL"
        )
        self.base.base_logger.info(f"{SECTION_SEPARATOR}\n")
    
    def _log_duplicate_header(self, report: Dict[str, Any]):
        """
        Log duplicate analysis header.
        
        Args:
            report: Duplicate analysis report
        """
        total = report['total_duplicate_groups']
        facts = report['total_duplicate_facts']
        pct = report['duplicate_percentage']
        
        self.base.base_logger.warning(f"\n{SECTION_SEPARATOR}")
        self.base.base_logger.warning("DUPLICATE DETECTION ANALYSIS")
        self.base.base_logger.warning(SECTION_SEPARATOR)
        self.base.base_logger.warning(
            f"Found {total} duplicate group(s) affecting {facts} facts "
            f"({pct:.1f}% of source XBRL)"
        )
    
    def _log_duplicate_severity_breakdown(self, report: Dict[str, Any]):
        """
        Log severity breakdown.
        
        Args:
            report: Duplicate analysis report
        """
        counts = report['severity_counts']
        
        self.base.base_logger.warning("\nSeverity Breakdown:")
        
        # Log CRITICAL duplicates
        if counts.get('CRITICAL', 0) > 0:
            self.base.base_logger.error(
                f"  {DUPLICATE_SEVERITY_LABELS['CRITICAL']} "
                f"(>5% variance): {counts['CRITICAL']} - "
                "SEVERE DATA ISSUES"
            )
        else:
            self.base.base_logger.info("  [OK] CRITICAL: 0")
        
        # Log MAJOR duplicates
        if counts.get('MAJOR', 0) > 0:
            self.base.base_logger.warning(
                f"  {DUPLICATE_SEVERITY_LABELS['MAJOR']} "
                f"(1-5% variance): {counts['MAJOR']} - "
                "Review recommended"
            )
        else:
            self.base.base_logger.info("  [OK] MAJOR: 0")
        
        # Log MINOR and REDUNDANT
        self.base.base_logger.info(
            f"  • MINOR (<1% variance): {counts.get('MINOR', 0)}"
        )
        self.base.base_logger.info(
            f"  • REDUNDANT (exact match): {counts.get('REDUNDANT', 0)}"
        )
    
    def _log_duplicate_quality_assessment(self, report: Dict[str, Any]):
        """
        Log overall quality assessment.
        
        Args:
            report: Duplicate analysis report
        """
        assessment = report.get('quality_assessment', '')
        
        self.base.base_logger.warning("\nQuality Assessment:")
        
        if report.get('has_critical_duplicates'):
            self.base.base_logger.error(f"  [!] {assessment}")
        elif report.get('has_major_duplicates'):
            self.base.base_logger.warning(f"  [!] {assessment}")
        else:
            self.base.base_logger.info(f"  [i] {assessment}")
    
    def _log_critical_duplicate_details(self, report: Dict[str, Any]):
        """
        Log critical duplicate details.
        
        Args:
            report: Duplicate analysis report
        """
        critical = report.get('critical_findings', [])
        
        if not critical:
            return
        
        self.base.base_logger.error(f"\n{SECTION_SEPARATOR}")
        self.base.base_logger.error(
            "CRITICAL DUPLICATES - DATA INTEGRITY ISSUES"
        )
        self.base.base_logger.error(SECTION_SEPARATOR)
        self.base.base_logger.error(
            "[!] WARNING: These duplicates indicate serious "
            "data quality problems."
        )
        self.base.base_logger.error(
            "Consider excluding this filing from financial analysis.\n"
        )
        
        for idx, finding in enumerate(
            critical[:MAX_DISPLAY_DUPLICATES], 1
        ):
            variance_pct = finding.get('variance_percentage', 0) * 100
            variance_amt = finding.get('max_variance_amount', 0)
            
            self.base.base_logger.error(
                f"{idx}. Concept: {finding['concept']}\n"
                f"   Context: {finding['context']}\n"
                f"   Duplicate Values: {finding['unique_values']}\n"
                f"   Variance: {variance_pct:.2f}% "
                f"(${variance_amt:,.0f})\n"
                f"   Duplicate Count: {finding['duplicate_count']} "
                f"instances\n"
            )
    
    def _log_major_duplicate_details(self, report: Dict[str, Any]):
        """
        Log major duplicate details.
        
        Args:
            report: Duplicate analysis report
        """
        major = report.get('major_findings', [])
        
        if not major:
            return
        
        self.base.base_logger.warning(f"\n{SECTION_SEPARATOR}")
        self.base.base_logger.warning(
            "MAJOR DUPLICATES - REVIEW RECOMMENDED"
        )
        self.base.base_logger.warning(SECTION_SEPARATOR)
        self.base.base_logger.warning(
            "These duplicates show significant variance. "
            "Manual review advised.\n"
        )
        
        for idx, finding in enumerate(
            major[:MAX_DISPLAY_DUPLICATES], 1
        ):
            variance_pct = finding.get('variance_percentage', 0) * 100
            
            self.base.base_logger.warning(
                f"{idx}. Concept: {finding['concept']}\n"
                f"   Values: {finding['unique_values']}\n"
                f"   Variance: {variance_pct:.2f}%\n"
            )
    
    def _log_duplicate_footer(self):
        """Log duplicate analysis footer."""
        self.base.base_logger.warning(f"{SECTION_SEPARATOR}\n")