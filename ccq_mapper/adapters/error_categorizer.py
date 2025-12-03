"""
Error Categorization Utilities
===============================

Location: ccq_val/engines/ccq_mapper/adapters/error_categorizer.py

Utilities for categorizing and analyzing errors.

Functions:
- extract_namespace: Extract namespace from qualified name
- categorize_error: Categorize error by type
- check_missing_fields: Identify missing required fields
"""

from typing import List, Dict, Any


def extract_namespace(qname: str) -> str:
    """
    Extract namespace prefix from qualified name.
    
    Args:
        qname: Qualified name (e.g., 'us-gaap:Assets')
        
    Returns:
        Namespace prefix (e.g., 'us-gaap') or empty string
    """
    if ':' in qname:
        return qname.split(':', 1)[0]
    return ''


def categorize_error(error_msg: str) -> str:
    """
    Categorize error message into standard types.
    
    Args:
        error_msg: Error message text
        
    Returns:
        Error category string
    """
    error_lower = error_msg.lower()
    
    # Check for missing field errors
    if 'missing' in error_lower:
        if 'concept' in error_lower or 'qname' in error_lower:
            return 'missing_concept_id'
        elif 'value' in error_lower:
            return 'missing_value'
        elif 'unit' in error_lower:
            return 'missing_unit'
        elif 'context' in error_lower:
            return 'missing_context'
        else:
            return 'missing_field'
    
    # Check for invalid data errors
    if 'invalid' in error_lower:
        return 'invalid_data'
    
    # Check for validation errors
    if 'validation' in error_lower or 'valid' in error_lower:
        return 'validation_error'
    
    return 'other'


def check_missing_fields_map_pro(fact: Dict[str, Any]) -> List[str]:
    """
    Check for missing required fields in Map Pro fact.
    
    Args:
        fact: Map Pro fact dictionary
        
    Returns:
        List of missing field names
    """
    missing = []
    
    if not fact.get('concept'):
        missing.append('concept')
    if not fact.get('value'):
        missing.append('value')
    if not fact.get('unit'):
        missing.append('unit')
    if not fact.get('context'):
        missing.append('context')
    
    return missing


def check_missing_fields_ccq(item: Dict[str, Any]) -> List[str]:
    """
    Check for missing required fields in CCQ item.
    
    Args:
        item: CCQ line item dictionary
        
    Returns:
        List of missing field names
    """
    missing = []
    
    if not item.get('qname'):
        missing.append('qname')
    if not item.get('value'):
        missing.append('value')
    if not item.get('properties'):
        missing.append('properties')
    if not item.get('classification'):
        missing.append('classification')
    
    return missing