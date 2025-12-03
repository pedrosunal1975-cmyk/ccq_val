"""
Duplicate Detection Logger
===========================

Location: ccq_val/engines/ccq_mapper/analysis/duplicate_logger_util.py

Logging utilities for duplicate detection.

Functions:
- log_duplicate_summary: Log summary of duplicate analysis
- log_critical_findings: Log critical duplicate details
- log_major_findings: Log major duplicate details
- log_clean_filing: Log message for clean filing

Features:
- Structured duplicate logging
- Severity-appropriate log levels
- Detailed findings output
"""

from typing import Dict, Any

from core.system_logger import get_logger

from .duplicate_constants import (
    SEPARATOR_LENGTH,
    MAX_DUPLICATES_DETAIL_LOG,
    SEVERITY_CRITICAL,
    SEVERITY_MAJOR,
    SEVERITY_MINOR,
    SEVERITY_REDUNDANT
)

logger = get_logger(__name__)


def log_clean_filing(total_facts: int):
    """
    Log message for clean filing with no duplicates.
    
    Args:
        total_facts: Total number of facts analyzed
    """
    logger.info(f"[OK] No duplicates found - clean source XBRL")


def log_duplicate_summary(report: Dict[str, Any]):
    """
    Log summary of duplicate analysis.
    
    Args:
        report: Duplicate analysis report
    """
    total = report['total_duplicate_groups']
    
    if total == 0:
        log_clean_filing(report['total_facts_analyzed'])
        return
    
    severity_counts = report['severity_counts']
    
    logger.warning(f"\n{'='*SEPARATOR_LENGTH}")
    logger.warning("DUPLICATE DETECTION SUMMARY")
    logger.warning(f"{'='*SEPARATOR_LENGTH}")
    logger.warning(f"Total duplicate groups found: {total}")
    logger.warning(
        f"  - CRITICAL (>5% variance): "
        f"{severity_counts[SEVERITY_CRITICAL]}"
    )
    logger.warning(
        f"  - MAJOR (1-5% variance): "
        f"{severity_counts[SEVERITY_MAJOR]}"
    )
    logger.warning(
        f"  - MINOR (<1% variance): "
        f"{severity_counts[SEVERITY_MINOR]}"
    )
    logger.warning(
        f"  - REDUNDANT (exact match): "
        f"{severity_counts[SEVERITY_REDUNDANT]}"
    )
    logger.warning("\nQuality Assessment:")
    logger.warning(f"  {report['quality_assessment']}")
    
    # Log detailed findings if present
    if report['has_critical_duplicates']:
        log_critical_findings(report['critical_findings'])
    
    if report['has_major_duplicates']:
        log_major_findings(report['major_findings'])
    
    logger.warning(f"\n{'='*SEPARATOR_LENGTH}\n")


def log_critical_findings(findings: list):
    """
    Log critical duplicate findings in detail.
    
    Args:
        findings: List of critical duplicate findings
    """
    logger.error(f"\n{'='*SEPARATOR_LENGTH}")
    logger.error("[!] CRITICAL DUPLICATES DETECTED - DATA INTEGRITY ISSUES")
    logger.error(f"{'='*SEPARATOR_LENGTH}")
    
    for idx, finding in enumerate(
        findings[:MAX_DUPLICATES_DETAIL_LOG], 1
    ):
        variance_pct = finding['variance_percentage'] * 100
        variance_amt = finding['max_variance_amount']
        
        logger.error(
            f"\n{idx}. Concept: {finding['concept']}\n"
            f"   Context: {finding['context']}\n"
            f"   Values: {finding['unique_values']}\n"
            f"   Variance: {variance_pct:.2f}% (${variance_amt:,.0f})\n"
            f"   Severity: {finding['severity']}"
        )


def log_major_findings(findings: list):
    """
    Log major duplicate findings.
    
    Args:
        findings: List of major duplicate findings
    """
    logger.warning(f"\n{'='*SEPARATOR_LENGTH}")
    logger.warning("[!] MAJOR DUPLICATES - REVIEW RECOMMENDED")
    logger.warning(f"{'='*SEPARATOR_LENGTH}")
    
    for idx, finding in enumerate(
        findings[:MAX_DUPLICATES_DETAIL_LOG], 1
    ):
        variance_pct = finding['variance_percentage'] * 100
        
        logger.warning(
            f"\n{idx}. Concept: {finding['concept']}\n"
            f"   Context: {finding['context']}\n"
            f"   Values: {finding['unique_values']}\n"
            f"   Variance: {variance_pct:.2f}%"
        )


def log_analysis_start(fact_count: int):
    """
    Log start of duplicate analysis.
    
    Args:
        fact_count: Number of facts to analyze
    """
    logger.info(f"Analyzing {fact_count} facts for duplicates...")


def log_analysis_complete(duplicate_count: int):
    """
    Log completion of duplicate analysis.
    
    Args:
        duplicate_count: Number of duplicate groups found
    """
    if duplicate_count == 0:
        logger.info("✓ No duplicates found in source XBRL")
    else:
        logger.warning(
            f"Found {duplicate_count} duplicate groups requiring analysis"
        )