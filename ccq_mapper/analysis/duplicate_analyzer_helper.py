"""
Duplicate Analysis Helper
==========================

Location: ccq_val/engines/ccq_mapper/analysis/duplicate_analyzer_helper.py

Helper functions for analyzing individual duplicate groups.

Functions:
- analyze_single_duplicate: Analyze one duplicate group
- build_duplicate_finding: Create finding dictionary
- extract_duplicate_metadata: Extract metadata from duplicate facts

Features:
- Complete duplicate characterization
- Severity classification
- Metadata extraction
"""

from typing import Dict, Any, List

from .fact_extractor import extract_values, extract_fact_metadata
from .variance_calculator import calculate_variance, classify_severity


def analyze_single_duplicate(
    concept: str,
    context: str,
    facts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze a single duplicate group.
    
    Extracts values, calculates variance, and classifies severity
    for a group of duplicate facts.
    
    Args:
        concept: Concept identifier
        context: Context identifier
        facts: List of duplicate facts
        
    Returns:
        Duplicate finding dictionary with analysis results
    """
    # Extract values
    values = extract_values(facts)
    unique_values = list(set(values))
    
    # Calculate variance if numeric
    variance_pct, max_variance = calculate_variance(values)
    
    # Classify severity
    severity = classify_severity(variance_pct, unique_values)
    
    # Extract metadata
    metadata = extract_duplicate_metadata(facts)
    
    # Truncate long context for display
    display_context = (
        context[:60] + '...' if len(context) > 60 else context
    )
    
    return {
        'concept': concept,
        'context': display_context,
        'full_context': context,
        'duplicate_count': len(facts),
        'unique_values': unique_values,
        'values': values,
        'variance_percentage': variance_pct,
        'max_variance_amount': max_variance,
        'severity': severity,
        'fact_ids': metadata['fact_ids'],
        'decimals': metadata['decimals'],
        'units': metadata['units']
    }


def extract_duplicate_metadata(
    facts: List[Dict[str, Any]]
) -> Dict[str, List[Any]]:
    """
    Extract metadata from duplicate facts.
    
    Args:
        facts: List of duplicate facts
        
    Returns:
        Dictionary with metadata lists
    """
    fact_ids = []
    decimals = []
    units = []
    
    for idx, fact in enumerate(facts):
        metadata = extract_fact_metadata(fact, idx)
        fact_ids.append(metadata['fact_id'])
        decimals.append(metadata['decimals'])
        units.append(metadata['unit'])
    
    return {
        'fact_ids': fact_ids,
        'decimals': decimals,
        'units': units
    }


def analyze_duplicate_groups(
    duplicate_groups: Dict[tuple, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Analyze all duplicate groups.
    
    Args:
        duplicate_groups: Dictionary of (concept, context) -> facts
        
    Returns:
        List of duplicate finding dictionaries
    """
    findings = []
    
    for (concept, context), facts in duplicate_groups.items():
        finding = analyze_single_duplicate(concept, context, facts)
        findings.append(finding)
    
    return findings


def separate_findings_by_severity(
    findings: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Separate findings by severity level.
    
    Args:
        findings: List of all duplicate findings
        
    Returns:
        Dictionary mapping severity to list of findings
    """
    from .duplicate_constants import (
        SEVERITY_CRITICAL,
        SEVERITY_MAJOR,
        SEVERITY_MINOR,
        SEVERITY_REDUNDANT
    )
    
    return {
        'critical': [f for f in findings if f['severity'] == SEVERITY_CRITICAL],
        'major': [f for f in findings if f['severity'] == SEVERITY_MAJOR],
        'minor': [f for f in findings if f['severity'] == SEVERITY_MINOR],
        'redundant': [f for f in findings if f['severity'] == SEVERITY_REDUNDANT]
    }