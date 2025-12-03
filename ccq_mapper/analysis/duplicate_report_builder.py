"""
Duplicate Report Builder
=========================

Location: ccq_val/engines/ccq_mapper/analysis/duplicate_report_builder.py

Builds comprehensive duplicate analysis reports.

Functions:
- build_duplicate_report: Create complete analysis report
- build_empty_report: Create report for clean filing (no duplicates)
- calculate_severity_counts: Count findings by severity
- generate_quality_assessment: Generate quality message
- calculate_duplicate_distribution: Distribution of duplicate counts

Features:
- Comprehensive report generation
- Statistical calculations
- Quality assessment messaging
"""

from typing import Dict, Any, List
from collections import defaultdict

from .duplicate_constants import (
    SEVERITY_CRITICAL,
    SEVERITY_MAJOR,
    SEVERITY_MINOR,
    SEVERITY_REDUNDANT
)


def calculate_severity_counts(
    findings: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Count findings by severity level.
    
    Args:
        findings: List of duplicate findings
        
    Returns:
        Dictionary mapping severity to count
    """
    counts = {
        SEVERITY_CRITICAL: 0,
        SEVERITY_MAJOR: 0,
        SEVERITY_MINOR: 0,
        SEVERITY_REDUNDANT: 0
    }
    
    for finding in findings:
        severity = finding['severity']
        counts[severity] = counts.get(severity, 0) + 1
    
    return counts


def calculate_duplicate_distribution(
    findings: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Calculate distribution of duplicate counts per group.
    
    Args:
        findings: List of duplicate findings
        
    Returns:
        Dictionary with duplicate count distribution
    """
    distribution = defaultdict(int)
    
    for finding in findings:
        count = finding['duplicate_count']
        distribution[count] += 1
    
    return {
        '2_copies': distribution.get(2, 0),
        '3_copies': distribution.get(3, 0),
        '4_copies': distribution.get(4, 0),
        '5_plus_copies': sum(v for k, v in distribution.items() if k >= 5)
    }


def generate_quality_assessment(
    severity_counts: Dict[str, int]
) -> str:
    """
    Generate overall quality assessment message.
    
    Args:
        severity_counts: Counts by severity level
        
    Returns:
        Quality assessment string
    """
    critical = severity_counts.get(SEVERITY_CRITICAL, 0)
    major = severity_counts.get(SEVERITY_MAJOR, 0)
    
    if critical > 0:
        return (
            f"SEVERE DATA INTEGRITY ISSUES: {critical} critical "
            f"duplicate(s) with material variance. Filing may contain "
            f"erroneous or fraudulent data. Recommend exclusion from analysis."
        )
    elif major > 0:
        return (
            f"SIGNIFICANT DATA QUALITY CONCERNS: {major} major "
            f"duplicate(s) with notable variance. Manual review "
            f"recommended before analysis."
        )
    elif severity_counts.get(SEVERITY_MINOR, 0) > 0:
        return (
            "Minor duplicate variances detected - likely formatting "
            "or rounding differences."
        )
    else:
        return (
            "Harmless redundant duplicates only - no data integrity concerns."
        )


def build_duplicate_report(
    findings: List[Dict[str, Any]],
    total_facts: int,
    metadata: Dict[str, Any],
    source_report: Dict[str, Any] = None,
    comprehensive_analysis: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Build comprehensive duplicate analysis report.
    
    Args:
        findings: List of duplicate findings
        total_facts: Total number of facts analyzed
        metadata: Filing metadata
        source_report: Optional source attribution report
        comprehensive_analysis: Optional comprehensive analysis
        
    Returns:
        Complete duplicate report dictionary
    """
    # Count by severity
    severity_counts = calculate_severity_counts(findings)
    
    # Separate findings by severity
    critical = [f for f in findings if f['severity'] == SEVERITY_CRITICAL]
    major = [f for f in findings if f['severity'] == SEVERITY_MAJOR]
    minor = [f for f in findings if f['severity'] == SEVERITY_MINOR]
    redundant = [f for f in findings if f['severity'] == SEVERITY_REDUNDANT]
    
    # Calculate statistics
    total_duplicates = len(findings)
    duplicate_facts_count = sum(f['duplicate_count'] for f in findings)
    
    # Calculate distribution
    distribution = calculate_duplicate_distribution(findings)
    
    # Calculate average copies per group
    avg_copies = (
        duplicate_facts_count / total_duplicates 
        if total_duplicates > 0 else 0
    )
    
    report = {
        'total_facts_analyzed': total_facts,
        'total_duplicate_groups': total_duplicates,
        'total_duplicate_facts': duplicate_facts_count,
        'duplicate_percentage': round(
            duplicate_facts_count / total_facts * 100, 2
        ) if total_facts > 0 else 0.0,
        
        # Explanation of groups vs facts relationship
        'duplicate_explanation': {
            'description': (
                'Groups represent unique (concept, context) pairs with '
                'duplicates. Facts represent total fact records involved.'
            ),
            'unique_duplicate_situations': total_duplicates,
            'total_facts_involved': duplicate_facts_count,
            'average_copies_per_group': round(avg_copies, 2),
            'distribution': distribution,
            'example': (
                f'If 130 groups each have 2 facts, that equals '
                f'{130 * 2} facts. But some groups have 3+ copies, '
                f'totaling {duplicate_facts_count} facts.'
            )
        },
        
        'severity_counts': severity_counts,
        'has_critical_duplicates': len(critical) > 0,
        'has_major_duplicates': len(major) > 0,
        'critical_findings': critical,
        'major_findings': major,
        'minor_findings': minor,
        'redundant_findings': redundant,
        'all_findings': findings,
        'filing_metadata': {
            'filing_id': metadata.get('filing_id', 'unknown'),
            'filing_date': metadata.get('filing_date', 'unknown'),
            'company': metadata.get('company', 'unknown')
        },
        'quality_assessment': generate_quality_assessment(severity_counts)
    }
    
    # Add source attribution if available
    if source_report:
        report['source_attribution'] = source_report.get(
            'source_breakdown', {}
        )
        report['source_details'] = source_report
    
    # Add comprehensive analysis if available
    if comprehensive_analysis:
        report['comprehensive_analysis'] = comprehensive_analysis
    
    return report


def build_empty_report(total_facts: int) -> Dict[str, Any]:
    """
    Build empty report when no duplicates found.
    
    Args:
        total_facts: Total number of facts analyzed
        
    Returns:
        Empty duplicate report (clean filing)
    """
    return {
        'total_facts_analyzed': total_facts,
        'total_duplicate_groups': 0,
        'total_duplicate_facts': 0,
        'duplicate_percentage': 0.0,
        'severity_counts': {
            SEVERITY_CRITICAL: 0,
            SEVERITY_MAJOR: 0,
            SEVERITY_MINOR: 0,
            SEVERITY_REDUNDANT: 0
        },
        'has_critical_duplicates': False,
        'has_major_duplicates': False,
        'critical_findings': [],
        'major_findings': [],
        'minor_findings': [],
        'redundant_findings': [],
        'all_findings': [],
        'filing_metadata': {},
        'quality_assessment': 'No duplicates detected - clean XBRL filing.'
    }