"""
Variance Calculator
===================

Location: ccq_val/engines/ccq_mapper/analysis/variance_calculator.py

Calculates variance between duplicate fact values.

Functions:
- calculate_variance: Calculate percentage and absolute variance
- convert_to_numeric: Convert values to Decimal for calculation
- classify_severity: Classify variance severity

Features:
- Handles numeric and non-numeric values
- Calculates percentage variance safely
- Avoids division by zero
"""

from typing import Dict, List, Any, Tuple
from decimal import Decimal, InvalidOperation

from .duplicate_constants import (
    CRITICAL_VARIANCE_THRESHOLD,
    MAJOR_VARIANCE_THRESHOLD,
    MINOR_VARIANCE_THRESHOLD,
    SEVERITY_CRITICAL,
    SEVERITY_MAJOR,
    SEVERITY_MINOR,
    SEVERITY_REDUNDANT
)


def convert_to_numeric(values: List[Any]) -> List[Decimal]:
    """
    Convert values to Decimal for numeric calculation.
    
    Args:
        values: List of values (may be numeric or non-numeric)
        
    Returns:
        List of Decimal values (excludes non-numeric)
    """
    numeric_values = []
    
    for val in values:
        try:
            if val is None or val == '':
                continue
            numeric_val = Decimal(str(val))
            numeric_values.append(numeric_val)
        except (InvalidOperation, ValueError, TypeError):
            # Skip non-numeric values
            continue
    
    return numeric_values


def calculate_variance(values: List[Any]) -> Tuple[float, float]:
    """
    Calculate variance between duplicate values.
    
    Calculates both percentage variance and absolute variance amount.
    Returns (0.0, 0.0) for non-numeric or single values.
    
    Args:
        values: List of values (may be numeric or non-numeric)
        
    Returns:
        Tuple of (variance_percentage, max_variance_amount)
        - variance_percentage: 0.0 to 1.0+ (e.g., 0.05 = 5%)
        - max_variance_amount: Absolute difference between min and max
    """
    # Convert to numeric
    numeric_values = convert_to_numeric(values)
    
    # Need at least 2 numeric values to calculate variance
    if len(numeric_values) < 2:
        return 0.0, 0.0
    
    # Calculate min, max, and variance amount
    min_val = min(numeric_values)
    max_val = max(numeric_values)
    variance_amount = abs(max_val - min_val)
    
    # Handle zero values
    if min_val == 0 and max_val == 0:
        return 0.0, 0.0
    
    # Calculate percentage variance relative to larger absolute value
    # This avoids inflating percentages for negative values
    base = max(abs(min_val), abs(max_val))
    
    if base == 0:
        return 0.0, float(variance_amount)
    
    variance_pct = float(variance_amount / base)
    
    return variance_pct, float(variance_amount)


def classify_severity(
    variance_pct: float,
    unique_values: List[Any]
) -> str:
    """
    Classify duplicate severity based on variance.
    
    Severity levels:
    - CRITICAL: >5% variance - severe data integrity issue
    - MAJOR: 1-5% variance - significant quality concern
    - MINOR: <1% variance - likely formatting/rounding
    - REDUNDANT: Exact match - harmless duplicate
    
    Args:
        variance_pct: Variance percentage (0.0 to 1.0+)
        unique_values: List of unique values
        
    Returns:
        Severity level string
    """
    # All values identical -> REDUNDANT
    if len(unique_values) == 1:
        return SEVERITY_REDUNDANT
    
    # Non-numeric or zero variance -> MINOR
    if variance_pct == 0.0:
        return SEVERITY_MINOR
    
    # Classify by variance threshold
    if variance_pct >= CRITICAL_VARIANCE_THRESHOLD:
        return SEVERITY_CRITICAL
    elif variance_pct >= MAJOR_VARIANCE_THRESHOLD:
        return SEVERITY_MAJOR
    else:
        return SEVERITY_MINOR


def calculate_variance_statistics(
    variance_pct: float,
    variance_amount: float,
    values: List[Any]
) -> Dict[str, Any]:
    """
    Calculate detailed variance statistics.
    
    Args:
        variance_pct: Variance percentage
        variance_amount: Absolute variance amount
        values: List of all values
        
    Returns:
        Dictionary with variance statistics
    """
    numeric_values = convert_to_numeric(values)
    
    if not numeric_values:
        return {
            'variance_pct': 0.0,
            'variance_amount': 0.0,
            'min_value': None,
            'max_value': None,
            'avg_value': None,
            'is_numeric': False
        }
    
    return {
        'variance_pct': variance_pct,
        'variance_amount': variance_amount,
        'min_value': float(min(numeric_values)),
        'max_value': float(max(numeric_values)),
        'avg_value': float(sum(numeric_values) / len(numeric_values)),
        'is_numeric': True
    }