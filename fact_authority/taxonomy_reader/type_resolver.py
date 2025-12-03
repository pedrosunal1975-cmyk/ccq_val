"""
Type Resolver
=============

Resolves and validates XBRL data types with fine-grained rules.

Provides detailed type information including:
- Base type (string, decimal, integer, boolean, date)
- Restrictions (min/max values, patterns, precision)
- Unit requirements (currency, shares, pure)
- Format rules (fraction digits, decimal places)

This enables precise data validation beyond basic type classification.

Classes:
    TypeResolver: Resolves data types and validation rules
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .type_definitions import STANDARD_XBRL_TYPES
from .type_classifier import classify_base_type, extract_local_type_name
from .type_schema_parser import (
    parse_custom_types_from_schema,
    parse_custom_types_from_multiple_schemas
)
from .type_validator import validate_value as validate_value_func


class TypeResolver:
    """
    Resolves XBRL data types and their validation rules.
    
    Analyzes schema type definitions to extract detailed validation
    rules including base types, restrictions, and format requirements.
    
    Works with both standard XBRL types (monetaryItemType, sharesItemType)
    and custom types defined in taxonomy schemas.
    
    This class provides a backward-compatible interface that delegates
    to specialized modules for classification, parsing, and validation.
    """
    
    def __init__(self):
        """Initialize type resolver."""
        self.custom_types: Dict[str, Dict[str, Any]] = {}
    
    def resolve_type(self, type_string: str) -> Dict[str, Any]:
        """
        Resolve a type string to its detailed properties.
        
        Args:
            type_string: Type string (e.g., 'xbrli:monetaryItemType')
            
        Returns:
            Dictionary with type properties:
            {
                'name': 'monetaryItemType',
                'base': 'decimal',
                'unit_required': True,
                'unit_type': 'currency',
                'fraction_digits': None,
                'restrictions': {...}
            }
        """
        if not type_string:
            return self._unknown_type()
        
        # Extract local type name
        local_type = extract_local_type_name(type_string)
        
        # Check standard types
        if local_type in STANDARD_XBRL_TYPES:
            type_info = STANDARD_XBRL_TYPES[local_type].copy()
            type_info['name'] = local_type
            type_info['standard'] = True
            return type_info
        
        # Check custom types cache
        if type_string in self.custom_types:
            return self.custom_types[type_string]
        
        # Unknown type - return basic info
        return self._unknown_type(local_type)
    
    def _unknown_type(self, name: str = 'unknown') -> Dict[str, Any]:
        """
        Create unknown type placeholder.
        
        Args:
            name: Type name
            
        Returns:
            Basic type info dictionary
        """
        return {
            'name': name,
            'base': 'string',
            'unit_required': False,
            'standard': False,
        }
    
    def extract_custom_types(self, schema_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Extract custom type definitions from a schema.
        
        Args:
            schema_path: Path to .xsd schema file
            
        Returns:
            Dictionary of custom type definitions
        """
        return parse_custom_types_from_schema(schema_path)
    
    def extract_from_multiple_schemas(
        self,
        schema_paths: List[Path]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract custom types from multiple schemas.
        
        Args:
            schema_paths: List of schema file paths
            
        Returns:
            Combined dictionary of custom types
        """
        all_types = parse_custom_types_from_multiple_schemas(schema_paths)
        
        # Cache the custom types
        self.custom_types = all_types
        
        return all_types
    
    def validate_value(
        self,
        value: Any,
        type_info: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a value against type constraints.
        
        Args:
            value: Value to validate
            type_info: Type information dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return validate_value_func(value, type_info)