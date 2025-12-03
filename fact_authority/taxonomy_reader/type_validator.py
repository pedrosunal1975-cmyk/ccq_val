"""
Type Validator
==============

Validates values against XBRL type constraints.

Performs validation of data values to ensure they conform to
their type definitions and restrictions.

Functions:
    validate_value: Main validation entry point
    validate_numeric_value: Validate numeric types
    validate_string_value: Validate string types
    validate_boolean_value: Validate boolean types
"""

from typing import Dict, List, Optional, Tuple, Any


def validate_value(value: Any, type_info: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a value against type constraints.
    
    Args:
        value: Value to validate
        type_info: Type information dictionary with 'base' and 'restrictions'
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if value conforms to type
        - error_message: None if valid, otherwise description of violation
    """
    base = type_info.get('base', 'string')
    restrictions = type_info.get('restrictions', {})
    
    if base in ['decimal', 'integer']:
        return validate_numeric_value(value, restrictions)
    elif base == 'string':
        return validate_string_value(value, restrictions)
    elif base == 'boolean':
        return validate_boolean_value(value)
    
    # Other types (date, anyURI) - no validation yet
    return True, None


def validate_numeric_value(
    value: Any,
    restrictions: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Validate a numeric value against restrictions.
    
    Checks:
    - Value is numeric
    - Min/max inclusive bounds
    - Fraction digits (decimal places)
    
    Args:
        value: Value to validate
        restrictions: Dictionary of numeric restrictions
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if value is numeric
    try:
        num_value = float(value)
    except (ValueError, TypeError):
        return False, f"Value '{value}' is not numeric"
    
    # Check minimum inclusive
    if 'min_inclusive' in restrictions:
        min_val = restrictions['min_inclusive']
        if num_value < min_val:
            return False, f"Value {num_value} below minimum {min_val}"
    
    # Check maximum inclusive
    if 'max_inclusive' in restrictions:
        max_val = restrictions['max_inclusive']
        if num_value > max_val:
            return False, f"Value {num_value} above maximum {max_val}"
    
    # Check fraction digits (decimal places)
    if 'fraction_digits' in restrictions:
        max_decimals = restrictions['fraction_digits']
        if max_decimals == 0 and num_value != int(num_value):
            return False, "Value must be integer (no decimals)"
    
    return True, None


def validate_string_value(
    value: Any,
    restrictions: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Validate a string value against restrictions.
    
    Checks:
    - Minimum length
    - Maximum length
    - Exact length
    
    Args:
        value: Value to validate
        restrictions: Dictionary of string restrictions
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    str_value = str(value)
    
    # Check minimum length
    if 'min_length' in restrictions:
        min_len = restrictions['min_length']
        if len(str_value) < min_len:
            return False, f"String too short (min {min_len})"
    
    # Check maximum length
    if 'max_length' in restrictions:
        max_len = restrictions['max_length']
        if len(str_value) > max_len:
            return False, f"String too long (max {max_len})"
    
    # Check exact length
    if 'length' in restrictions:
        exact_len = restrictions['length']
        if len(str_value) != exact_len:
            return False, f"String must be exactly {exact_len} characters"
    
    return True, None


def validate_boolean_value(value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate a boolean value.
    
    Accepts: True, False, 'true', 'false', '1', '0'
    
    Args:
        value: Value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_boolean_values = [True, False, 'true', 'false', '1', '0']
    
    if value not in valid_boolean_values:
        return False, f"Value '{value}' is not boolean"
    
    return True, None