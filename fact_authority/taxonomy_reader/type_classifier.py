"""
Type Classifier
===============

Classifies and categorizes XBRL data types.

Provides classification logic to determine base type categories
from type strings and extract namespace information from URIs.

Functions:
    classify_base_type: Classify type string to base category
    extract_namespace_prefix: Extract prefix from namespace URI
"""

from typing import Any, Dict, Optional, Tuple
from .type_definitions import STANDARD_XBRL_TYPES, XSD_TYPE_CATEGORIES


# Constants for namespace extraction
YEAR_STRING_LENGTH = 4
MIN_URI_PARTS_FOR_PREFIX = 2
MIN_URI_PARTS_WITH_YEAR = 3


def classify_base_type(type_string: str, custom_types: Optional[dict] = None) -> str:
    """
    Classify a type string into a base category.
    
    Uses lookup tables instead of nested if-elif chains for O(1) classification.
    
    Args:
        type_string: Full type string (e.g., 'xbrli:monetaryItemType')
        custom_types: Optional dict of custom type definitions
        
    Returns:
        Base type category: 'decimal', 'integer', 'string', 'boolean',
        'date', 'anyURI', or 'string' (default)
    """
    if not type_string:
        return 'string'
    
    # Extract local name (after colon)
    local_type = type_string.split(':')[1] if ':' in type_string else type_string
    
    # Check XSD built-in types first (most common)
    if local_type in XSD_TYPE_CATEGORIES:
        return XSD_TYPE_CATEGORIES[local_type]
    
    # Check standard XBRL types
    if local_type in STANDARD_XBRL_TYPES:
        return STANDARD_XBRL_TYPES[local_type]['base']
    
    # Check custom types if provided
    if custom_types and type_string in custom_types:
        return custom_types[type_string].get('base', 'string')
    
    # Default fallback
    return 'string'


def extract_namespace_prefix(namespace_uri: str) -> str:
    """
    Extract namespace prefix from a namespace URI.
    
    Derives a prefix from the URI structure. Examples:
    - 'http://fasb.org/us-gaap/2025' -> 'us-gaap'
    - 'http://xbrl.sec.gov/dei/2024' -> 'dei'
    - 'http://xbrl.org/2003/instance' -> 'instance'
    
    Args:
        namespace_uri: Full namespace URI
        
    Returns:
        Namespace prefix (empty string if cannot determine)
    """
    if not namespace_uri:
        return ''
    
    # Remove trailing slash and split
    uri = namespace_uri.rstrip('/')
    parts = uri.split('/')
    
    if len(parts) < MIN_URI_PARTS_FOR_PREFIX:
        # Not enough parts to extract meaningful prefix
        return parts[-1] if parts else ''
    
    last_part = parts[-1]
    
    # Check if last part is a year (e.g., '2025')
    if last_part.isdigit() and len(last_part) == YEAR_STRING_LENGTH:
        # Year found, use second-to-last part as prefix
        if len(parts) >= MIN_URI_PARTS_WITH_YEAR:
            return parts[-2]
    else:
        # Last part is not a year, use it as prefix
        return last_part
    
    # Fallback to last part
    return parts[-1] if parts else ''


def extract_local_type_name(type_string: str) -> str:
    """
    Extract local type name from qualified type string.
    
    Args:
        type_string: Type string (e.g., 'xbrli:monetaryItemType')
        
    Returns:
        Local name (e.g., 'monetaryItemType')
    """
    if not type_string:
        return ''
    
    return type_string.split(':')[1] if ':' in type_string else type_string