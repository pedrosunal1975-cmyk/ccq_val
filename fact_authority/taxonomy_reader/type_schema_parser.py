"""
Type Schema Parser
==================

Parses custom type definitions from XBRL schema files.

Extracts simpleType and complexType definitions from XSD files,
including their base types and restriction facets.

Functions:
    parse_custom_types_from_schema: Extract types from single schema
    parse_custom_types_from_multiple_schemas: Extract from multiple schemas
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import xml.etree.ElementTree as ET
import logging

from .type_definitions import XML_NAMESPACES
from .type_classifier import classify_base_type, extract_namespace_prefix


logger = logging.getLogger(__name__)


# XSD facet name mappings
FACET_MAPPINGS = {
    'minInclusive': 'min_inclusive',
    'maxInclusive': 'max_inclusive',
    'minExclusive': 'min_exclusive',
    'maxExclusive': 'max_exclusive',
    'totalDigits': 'total_digits',
    'fractionDigits': 'fraction_digits',
    'length': 'length',
    'minLength': 'min_length',
    'maxLength': 'max_length',
    'pattern': 'pattern',
    'enumeration': 'enumeration',
}

# Facets that should be converted to floats
NUMERIC_FACETS = {'min_inclusive', 'max_inclusive', 'min_exclusive', 'max_exclusive'}

# Facets that should be converted to integers
INTEGER_FACETS = {'total_digits', 'fraction_digits', 'length', 'min_length', 'max_length'}


def parse_custom_types_from_schema(schema_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Extract custom type definitions from a schema file.
    
    Parses both simpleType and complexType definitions to build
    a dictionary of custom type information.
    
    Args:
        schema_path: Path to .xsd schema file
        
    Returns:
        Dictionary mapping qualified type names to type info:
        {
            'prefix:TypeName': {
                'name': 'TypeName',
                'base': 'decimal',
                'base_type_full': 'xsd:decimal',
                'unit_required': False,
                'standard': False,
                'restrictions': {...}
            }
        }
    """
    if not schema_path.exists():
        logger.warning(f"Schema file not found: {schema_path}")
        return {}
    
    custom_types = {}
    
    try:
        tree = ET.parse(schema_path)
        root = tree.getroot()
        
        # Get target namespace and derive prefix
        target_namespace = root.get('targetNamespace', '')
        namespace_prefix = extract_namespace_prefix(target_namespace)
        
        # Parse simpleType definitions
        simple_types = _parse_simple_types(root, namespace_prefix)
        custom_types.update(simple_types)
        
        # Parse complexType definitions
        complex_types = _parse_complex_types(root, namespace_prefix)
        custom_types.update(complex_types)
        
        logger.debug(f"Extracted {len(custom_types)} custom types from {schema_path.name}")
        
    except ET.ParseError as e:
        logger.error(f"Failed to parse schema {schema_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error parsing schema {schema_path}: {e}")
        return {}
    
    return custom_types


def parse_custom_types_from_multiple_schemas(
    schema_paths: List[Path]
) -> Dict[str, Dict[str, Any]]:
    """
    Extract custom types from multiple schema files.
    
    Args:
        schema_paths: List of schema file paths
        
    Returns:
        Combined dictionary of custom types from all schemas
    """
    all_types = {}
    
    for schema_path in schema_paths:
        try:
            types = parse_custom_types_from_schema(schema_path)
            all_types.update(types)
        except Exception as e:
            logger.error(f"Error extracting types from {schema_path}: {e}")
            continue
    
    logger.info(f"Extracted {len(all_types)} custom types from {len(schema_paths)} schemas")
    
    return all_types


def _parse_simple_types(root: ET.Element, namespace_prefix: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse all simpleType definitions from schema root.
    
    Args:
        root: Schema root element
        namespace_prefix: Namespace prefix for this schema
        
    Returns:
        Dictionary of simpleType definitions
    """
    simple_types = {}
    
    for simple_type in root.findall('.//xsd:simpleType', XML_NAMESPACES):
        type_name = simple_type.get('name')
        
        if type_name:
            type_info = _parse_simple_type_element(simple_type, type_name)
            
            if type_info:
                qname = f"{namespace_prefix}:{type_name}" if namespace_prefix else type_name
                simple_types[qname] = type_info
    
    return simple_types


def _parse_simple_type_element(
    simple_type: ET.Element,
    type_name: str
) -> Optional[Dict[str, Any]]:
    """
    Parse a single simpleType element.
    
    Args:
        simple_type: simpleType XML element
        type_name: Name of the type
        
    Returns:
        Type info dictionary or None if cannot parse
    """
    # Look for restriction
    restriction = simple_type.find('.//xsd:restriction', XML_NAMESPACES)
    
    if restriction is None:
        return None
    
    base_type = restriction.get('base', '')
    
    return {
        'name': type_name,
        'base': classify_base_type(base_type),
        'base_type_full': base_type,
        'unit_required': False,
        'standard': False,
        'restrictions': _extract_restrictions(restriction)
    }


def _parse_complex_types(root: ET.Element, namespace_prefix: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse all complexType definitions from schema root.
    
    Args:
        root: Schema root element
        namespace_prefix: Namespace prefix for this schema
        
    Returns:
        Dictionary of complexType definitions
    """
    complex_types = {}
    
    for complex_type in root.findall('.//xsd:complexType', XML_NAMESPACES):
        type_name = complex_type.get('name')
        
        if type_name:
            type_info = _parse_complex_type_element(complex_type, type_name)
            
            if type_info:
                qname = f"{namespace_prefix}:{type_name}" if namespace_prefix else type_name
                complex_types[qname] = type_info
    
    return complex_types


def _parse_complex_type_element(
    complex_type: ET.Element,
    type_name: str
) -> Optional[Dict[str, Any]]:
    """
    Parse a single complexType element.
    
    Args:
        complex_type: complexType XML element
        type_name: Name of the type
        
    Returns:
        Type info dictionary or None if cannot parse
    """
    # Look for simpleContent extension
    simple_content = complex_type.find('.//xsd:simpleContent', XML_NAMESPACES)
    
    if simple_content is None:
        return None
    
    extension = simple_content.find('.//xsd:extension', XML_NAMESPACES)
    
    if extension is None:
        return None
    
    base_type = extension.get('base', '')
    
    return {
        'name': type_name,
        'base': classify_base_type(base_type),
        'base_type_full': base_type,
        'unit_required': False,
        'standard': False,
        'complex': True,
    }


def _extract_restrictions(restriction: ET.Element) -> Dict[str, Any]:
    """
    Extract restriction facets from a restriction element.
    
    Args:
        restriction: XSD restriction element
        
    Returns:
        Dictionary of restriction facets with converted values
    """
    restrictions = {}
    
    for xsd_facet, our_key in FACET_MAPPINGS.items():
        for facet in restriction.findall(f'.//xsd:{xsd_facet}', XML_NAMESPACES):
            value = facet.get('value')
            
            if value:
                # Convert value to appropriate type
                converted_value = _convert_facet_value(our_key, value)
                
                # Handle enumeration specially (multiple values)
                if our_key == 'enumeration':
                    if our_key not in restrictions:
                        restrictions[our_key] = []
                    restrictions[our_key].append(converted_value)
                else:
                    restrictions[our_key] = converted_value
    
    return restrictions


def _convert_facet_value(facet_key: str, value: str) -> Any:
    """
    Convert a facet value to the appropriate Python type.
    
    Args:
        facet_key: Our internal facet key name
        value: String value from XSD
        
    Returns:
        Converted value (float, int, or string)
    """
    if facet_key in NUMERIC_FACETS:
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Invalid numeric value for {facet_key}: {value}")
            return value
    
    elif facet_key in INTEGER_FACETS:
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {facet_key}: {value}")
            return value
    
    return value