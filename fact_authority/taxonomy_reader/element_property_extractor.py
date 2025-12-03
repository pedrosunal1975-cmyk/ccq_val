"""
Element Property Extractor
===========================

Extracts comprehensive properties of XBRL concepts from schema files.

This is the foundation for validation - understanding what each concept IS:
- Is it monetary? Shares? Text?
- Is it instant (point in time) or duration (period)?
- Is it debit or credit?
- Is it abstract (header) or concrete (data)?

Classes:
    ElementPropertyExtractor: Extracts concept properties from XSD files
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import xml.etree.ElementTree as ET
import logging


logger = logging.getLogger(__name__)


class ElementPropertyExtractor:
    """
    Extracts element properties from XBRL schema files.
    
    Parses XSD files to extract comprehensive concept definitions including
    type, period, balance, abstract status, and other properties required
    for validation and understanding.
    
    Example element in schema:
        <element id="us-gaap_Cash"
                 name="Cash"
                 type="xbrli:monetaryItemType"
                 substitutionGroup="xbrli:item"
                 xbrli:periodType="instant"
                 xbrli:balance="debit"
                 abstract="false"
                 nillable="true"/>
    """
    
    # Standard XML namespaces
    NAMESPACES = {
        'xsd': 'http://www.w3.org/2001/XMLSchema',
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
    }
    
    # Standard XBRL item types
    MONETARY_TYPES = {
        'monetaryItemType',
        'monetaryAmountItemType',
    }
    
    SHARE_TYPES = {
        'sharesItemType',
    }
    
    NUMERIC_TYPES = {
        'decimalItemType',
        'integerItemType',
        'positiveIntegerItemType',
        'nonNegativeIntegerItemType',
    }
    
    TEXT_TYPES = {
        'stringItemType',
        'normalizedStringItemType',
        'tokenItemType',
    }
    
    DATE_TYPES = {
        'dateItemType',
        'dateTimeItemType',
    }
    
    BOOLEAN_TYPES = {
        'booleanItemType',
    }
    
    def __init__(self):
        """Initialize element property extractor."""
        pass
    
    def extract_from_schema(self, schema_path: Path) -> Dict[str, Dict[str, any]]:
        """
        Extract all element properties from a schema file.
        
        Args:
            schema_path: Path to .xsd schema file
            
        Returns:
            Dictionary mapping concept QNames to their properties:
            {
                'us-gaap:Cash': {
                    'id': 'us-gaap_Cash',
                    'name': 'Cash',
                    'type': 'xbrli:monetaryItemType',
                    'period_type': 'instant',
                    'balance': 'debit',
                    'abstract': False,
                    'nillable': True,
                    'base_type': 'monetary',
                    'substitution_group': 'xbrli:item',
                    'namespace': 'http://fasb.org/us-gaap/2025',
                    'schema_location': '/path/to/schema.xsd'
                }
            }
            
        Raises:
            FileNotFoundError: If schema file doesn't exist
        """
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        elements = {}
        
        try:
            tree = ET.parse(schema_path)
            root = tree.getroot()
            
            # Get target namespace from schema
            target_namespace = root.get('targetNamespace', '')
            
            # Extract namespace prefix for this schema
            namespace_prefix = self._extract_namespace_prefix(target_namespace)
            
            # Find all element definitions
            for element in root.findall('.//xsd:element', self.NAMESPACES):
                element_name = element.get('name')
                
                if element_name:
                    # Build qualified name
                    qname = f"{namespace_prefix}:{element_name}" if namespace_prefix else element_name
                    
                    # Extract all properties
                    properties = self._extract_element_properties(
                        element,
                        target_namespace,
                        schema_path
                    )
                    
                    if properties:
                        elements[qname] = properties
            
            logger.debug(f"Extracted {len(elements)} elements from {schema_path.name}")
            
        except ET.ParseError as e:
            logger.warning(f"Failed to parse schema {schema_path}: {e}")
            return {}
        
        return elements
    
    def _extract_element_properties(
        self,
        element: ET.Element,
        target_namespace: str,
        schema_path: Path
    ) -> Optional[Dict[str, any]]:
        """
        Extract all properties from an element definition.
        
        Args:
            element: XML element node
            target_namespace: Schema's target namespace
            schema_path: Path to schema file
            
        Returns:
            Dictionary of element properties or None if invalid
        """
        # Required attributes
        name = element.get('name')
        if not name:
            return None
        
        element_id = element.get('id', '')
        element_type = element.get('type', '')
        
        # XBRL-specific attributes (with namespace)
        period_type = element.get('{http://www.xbrl.org/2003/instance}periodType', '')
        balance = element.get('{http://www.xbrl.org/2003/instance}balance', '')
        
        # Standard XSD attributes
        abstract = element.get('abstract', 'false').lower() == 'true'
        nillable = element.get('nillable', 'false').lower() == 'true'
        substitution_group = element.get('substitutionGroup', '')
        
        # Resolve base type category
        base_type = self._classify_type(element_type)
        
        # Build properties dictionary
        properties = {
            'id': element_id,
            'name': name,
            'type': element_type,
            'period_type': period_type if period_type else None,
            'balance': balance if balance else None,
            'abstract': abstract,
            'nillable': nillable,
            'base_type': base_type,
            'substitution_group': substitution_group,
            'namespace': target_namespace,
            'schema_location': str(schema_path),
        }
        
        return properties
    
    def _extract_namespace_prefix(self, namespace_uri: str) -> str:
        """
        Extract namespace prefix from URI.
        
        Attempts to derive a sensible prefix from the namespace URI.
        E.g., 'http://fasb.org/us-gaap/2025' -> 'us-gaap'
        
        Args:
            namespace_uri: Full namespace URI
            
        Returns:
            Namespace prefix (best guess)
        """
        if not namespace_uri:
            return ''
        
        # Remove trailing slash
        uri = namespace_uri.rstrip('/')
        
        # Split by '/' and get last meaningful part
        parts = uri.split('/')
        
        # Common patterns:
        # http://fasb.org/us-gaap/2025 -> us-gaap
        # http://xbrl.sec.gov/dei/2024 -> dei
        # http://xbrl.org/2003/instance -> xbrli
        
        if len(parts) >= 2:
            # Check if last part is a year/version
            last_part = parts[-1]
            if last_part.isdigit() and len(last_part) == 4:
                # Version number, use second-to-last
                if len(parts) >= 3:
                    return parts[-2]
            else:
                # Use last part
                return last_part
        
        # Fallback: use last part
        if parts:
            return parts[-1]
        
        return ''
    
    def _classify_type(self, type_string: str) -> str:
        """
        Classify an element type into a base category.
        
        Args:
            type_string: Full type string (e.g., 'xbrli:monetaryItemType')
            
        Returns:
            Base type category: 'monetary', 'shares', 'numeric', 'text',
            'date', 'boolean', or 'unknown'
        """
        if not type_string:
            return 'unknown'
        
        # Extract local name (after colon)
        if ':' in type_string:
            local_type = type_string.split(':')[1]
        else:
            local_type = type_string
        
        # Classify by type
        if local_type in self.MONETARY_TYPES:
            return 'monetary'
        elif local_type in self.SHARE_TYPES:
            return 'shares'
        elif local_type in self.NUMERIC_TYPES:
            return 'numeric'
        elif local_type in self.TEXT_TYPES:
            return 'text'
        elif local_type in self.DATE_TYPES:
            return 'date'
        elif local_type in self.BOOLEAN_TYPES:
            return 'boolean'
        else:
            return 'unknown'
    
    def extract_from_multiple_schemas(
        self,
        schema_paths: List[Path]
    ) -> Dict[str, Dict[str, any]]:
        """
        Extract element properties from multiple schema files.
        
        Args:
            schema_paths: List of schema file paths
            
        Returns:
            Combined dictionary of all element properties
        """
        all_elements = {}
        
        for schema_path in schema_paths:
            try:
                elements = self.extract_from_schema(schema_path)
                
                # Merge, with later schemas overwriting earlier ones if duplicate
                all_elements.update(elements)
                
            except FileNotFoundError:
                logger.warning(f"Schema file not found: {schema_path}")
                continue
            except Exception as e:
                logger.error(f"Error extracting from {schema_path}: {e}")
                continue
        
        logger.info(f"Extracted {len(all_elements)} total elements from {len(schema_paths)} schemas")
        
        return all_elements
    
    def filter_by_type(
        self,
        elements: Dict[str, Dict[str, any]],
        base_type: str
    ) -> Dict[str, Dict[str, any]]:
        """
        Filter elements by base type.
        
        Args:
            elements: Dictionary of element properties
            base_type: Base type to filter by ('monetary', 'shares', etc.)
            
        Returns:
            Filtered dictionary containing only elements of specified type
        """
        return {
            qname: props
            for qname, props in elements.items()
            if props.get('base_type') == base_type
        }
    
    def filter_abstract(
        self,
        elements: Dict[str, Dict[str, any]],
        abstract: bool = True
    ) -> Dict[str, Dict[str, any]]:
        """
        Filter elements by abstract status.
        
        Args:
            elements: Dictionary of element properties
            abstract: If True, return abstract elements; if False, return concrete
            
        Returns:
            Filtered dictionary
        """
        return {
            qname: props
            for qname, props in elements.items()
            if props.get('abstract') == abstract
        }
    
    def filter_by_period(
        self,
        elements: Dict[str, Dict[str, any]],
        period_type: str
    ) -> Dict[str, Dict[str, any]]:
        """
        Filter elements by period type.
        
        Args:
            elements: Dictionary of element properties
            period_type: 'instant' or 'duration'
            
        Returns:
            Filtered dictionary
        """
        return {
            qname: props
            for qname, props in elements.items()
            if props.get('period_type') == period_type
        }
    
    def get_statistics(self, elements: Dict[str, Dict[str, any]]) -> Dict[str, int]:
        """
        Get statistics about extracted elements.
        
        Args:
            elements: Dictionary of element properties
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total': len(elements),
            'abstract': 0,
            'concrete': 0,
            'instant': 0,
            'duration': 0,
            'monetary': 0,
            'shares': 0,
            'numeric': 0,
            'text': 0,
            'debit_balance': 0,
            'credit_balance': 0,
        }
        
        for props in elements.values():
            if props.get('abstract'):
                stats['abstract'] += 1
            else:
                stats['concrete'] += 1
            
            period = props.get('period_type')
            if period == 'instant':
                stats['instant'] += 1
            elif period == 'duration':
                stats['duration'] += 1
            
            base_type = props.get('base_type')
            if base_type == 'monetary':
                stats['monetary'] += 1
            elif base_type == 'shares':
                stats['shares'] += 1
            elif base_type == 'numeric':
                stats['numeric'] += 1
            elif base_type == 'text':
                stats['text'] += 1
            
            balance = props.get('balance')
            if balance == 'debit':
                stats['debit_balance'] += 1
            elif balance == 'credit':
                stats['credit_balance'] += 1
        
        return stats