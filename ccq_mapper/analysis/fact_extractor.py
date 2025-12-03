"""
Fact Field Extractor
====================

Location: ccq_val/engines/ccq_mapper/analysis/fact_extractor.py

Market-agnostic field extraction from facts.

Functions:
- extract_concept: Extract concept identifier from fact
- extract_context: Extract context identifier from fact
- extract_values: Extract values from list of facts
- extract_fact_metadata: Extract metadata fields

Features:
- Tries multiple field names for market compatibility
- Handles missing or malformed data gracefully
- Returns None for missing fields
"""

from typing import Dict, Any, List, Optional

from .duplicate_constants import (
    CONCEPT_FIELD_NAMES,
    CONTEXT_FIELD_NAMES,
    VALUE_FIELD_NAMES
)


def extract_concept(fact: Dict[str, Any]) -> Optional[str]:
    """
    Extract concept identifier from fact.
    
    Tries multiple field names for market-agnostic extraction.
    CCQ typically uses 'concept' or 'concept_qname' in parsed facts.
    
    Args:
        fact: Fact dictionary
        
    Returns:
        Concept string or None if not found
    """
    for field in CONCEPT_FIELD_NAMES:
        concept = fact.get(field)
        if concept:
            return str(concept)
    return None


def extract_context(fact: Dict[str, Any]) -> Optional[str]:
    """
    Extract context identifier from fact.
    
    Tries multiple field names for market-agnostic extraction.
    CCQ typically uses 'context_ref' or 'context_id' in parsed facts.
    
    Args:
        fact: Fact dictionary
        
    Returns:
        Context string or None if not found
    """
    for field in CONTEXT_FIELD_NAMES:
        context = fact.get(field)
        if context:
            return str(context)
    return None


def extract_values(facts: List[Dict[str, Any]]) -> List[Any]:
    """
    Extract values from list of facts.
    
    Tries multiple field names for market-agnostic extraction.
    CCQ typically uses 'fact_value' or 'value' in parsed facts.
    
    Args:
        facts: List of fact dictionaries
        
    Returns:
        List of values (may be numeric or non-numeric)
    """
    values = []
    for fact in facts:
        for field in VALUE_FIELD_NAMES:
            value = fact.get(field)
            if value is not None:
                values.append(value)
                break
    return values


def extract_fact_metadata(fact: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Extract metadata fields from fact.
    
    Args:
        fact: Fact dictionary
        index: Fact index (used as fallback ID)
        
    Returns:
        Dictionary of metadata fields
    """
    return {
        'fact_id': fact.get('fact_id', index),
        'decimals': fact.get('decimals', 'unknown'),
        'unit': fact.get('unit_ref', fact.get('unit_id', 'unknown')),
        'period': fact.get('period', 'unknown')
    }