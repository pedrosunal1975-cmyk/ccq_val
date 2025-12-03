"""
Type Definitions
================

Standard XBRL type definitions and constants.

This module contains pure data - the standard XBRL type registry
with their properties, restrictions, and requirements.

Constants:
    STANDARD_XBRL_TYPES: Complete registry of standard XBRL types
    XML_NAMESPACES: Standard XML namespace mappings
"""

from typing import Dict, List, Optional, Tuple, Any


# Standard XML namespaces used in XBRL
XML_NAMESPACES = {
    'xsd': 'http://www.w3.org/2001/XMLSchema',
    'xbrli': 'http://www.xbrl.org/2003/instance',
}


# Standard XBRL type definitions with their properties
STANDARD_XBRL_TYPES: Dict[str, Dict[str, Any]] = {
    # Numeric types
    'monetaryItemType': {
        'base': 'decimal',
        'unit_required': True,
        'unit_type': 'currency',
        'fraction_digits': None,
    },
    'sharesItemType': {
        'base': 'decimal',
        'unit_required': True,
        'unit_type': 'shares',
        'fraction_digits': 0,
    },
    'decimalItemType': {
        'base': 'decimal',
        'unit_required': False,
        'fraction_digits': None,
    },
    'integerItemType': {
        'base': 'integer',
        'unit_required': False,
        'fraction_digits': 0,
    },
    'positiveIntegerItemType': {
        'base': 'integer',
        'unit_required': False,
        'fraction_digits': 0,
        'min_inclusive': 1,
    },
    'nonNegativeIntegerItemType': {
        'base': 'integer',
        'unit_required': False,
        'fraction_digits': 0,
        'min_inclusive': 0,
    },
    'percentItemType': {
        'base': 'decimal',
        'unit_required': True,
        'unit_type': 'pure',
        'fraction_digits': None,
    },
    'pureItemType': {
        'base': 'decimal',
        'unit_required': True,
        'unit_type': 'pure',
        'fraction_digits': None,
    },
    
    # String types
    'stringItemType': {
        'base': 'string',
        'unit_required': False,
    },
    'normalizedStringItemType': {
        'base': 'string',
        'unit_required': False,
        'normalized': True,
    },
    'tokenItemType': {
        'base': 'string',
        'unit_required': False,
        'normalized': True,
        'collapsed': True,
    },
    
    # Date types
    'dateItemType': {
        'base': 'date',
        'unit_required': False,
    },
    'dateTimeItemType': {
        'base': 'datetime',
        'unit_required': False,
    },
    
    # Boolean type
    'booleanItemType': {
        'base': 'boolean',
        'unit_required': False,
    },
    
    # Other types
    'anyURIItemType': {
        'base': 'anyURI',
        'unit_required': False,
    },
}


# XSD built-in type to base category mapping
XSD_TYPE_CATEGORIES = {
    # Decimal types
    'decimal': 'decimal',
    'float': 'decimal',
    'double': 'decimal',
    
    # Integer types
    'integer': 'integer',
    'int': 'integer',
    'long': 'integer',
    'short': 'integer',
    'byte': 'integer',
    'positiveInteger': 'integer',
    'negativeInteger': 'integer',
    'nonPositiveInteger': 'integer',
    'nonNegativeInteger': 'integer',
    'unsignedInt': 'integer',
    'unsignedLong': 'integer',
    
    # String types
    'string': 'string',
    'normalizedString': 'string',
    'token': 'string',
    
    # Boolean types
    'boolean': 'boolean',
    
    # Date types
    'date': 'date',
    'dateTime': 'date',
    'time': 'date',
    
    # URI types
    'anyURI': 'anyURI',
}