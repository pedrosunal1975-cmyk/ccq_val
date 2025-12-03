# File: extension_schema_parser.py
# Location: engines/fact_authority/filings_reader/extension_schema_parser.py

"""
Extension Schema Parser
=======================

Parses company extension XSD schema files to extract extension concepts.

Reads company-specific extension taxonomy schemas (company-YYYY.xsd) and
extracts:
- Extension namespace
- Extension concept definitions
- Element types and attributes
- Substitution groups

Works with XBRL taxonomy schemas following W3C XML Schema specification.

Classes:
    ExtensionSchemaParser: Parser for company extension schemas
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import logging
from lxml import etree


logger = logging.getLogger(__name__)


class ExtensionSchemaParser:
    """
    Parses company extension XSD schema files.
    
    Extracts extension concepts, namespaces, and element definitions from
    company-specific XBRL taxonomy extension schemas.
    
    Key features:
    - Namespace extraction
    - Element definition parsing
    - Type resolution
    - Substitution group identification
    """
    
    # XML namespaces used in XBRL schemas
    NAMESPACES = {
        'xsd': 'http://www.w3.org/2001/XMLSchema',
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink'
    }
    
    def __init__(self):
        """Initialize extension schema parser."""
        pass
    
    def parse(self, schema_path: Path) -> Dict[str, any]:
        """
        Parse extension schema file.
        
        Args:
            schema_path: Path to extension .xsd file
            
        Returns:
            Dictionary with extension metadata:
            {
                'namespace': Extension namespace URI,
                'namespace_prefix': Extension namespace prefix,
                'taxonomy_year': Year from filename,
                'elements': List of element definitions,
                'imports': List of imported schemas,
                'element_count': Number of elements
            }
            
        Raises:
            FileNotFoundError: If schema file not found
            ValueError: If schema cannot be parsed
        """
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        logger.info(f"Parsing extension schema: {schema_path.name}")
        
        try:
            # Parse XML
            tree = etree.parse(str(schema_path))
            root = tree.getroot()
            
            # Extract namespace
            namespace_info = self._extract_namespace(root, schema_path)
            
            # Extract elements
            elements = self._extract_elements(root, namespace_info['namespace'])
            
            # Extract imports
            imports = self._extract_imports(root)
            
            result = {
                'namespace': namespace_info['namespace'],
                'namespace_prefix': namespace_info['prefix'],
                'taxonomy_year': namespace_info.get('year'),
                'elements': elements,
                'imports': imports,
                'element_count': len(elements)
            }
            
            logger.info(
                f"Parsed extension schema: {len(elements)} elements, "
                f"namespace: {namespace_info['prefix']}"
            )
            
            return result
        
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XML in schema {schema_path}: {e}")
        
        except Exception as e:
            logger.error(f"Error parsing schema {schema_path}: {e}")
            raise
    
    def _extract_namespace(
        self,
        root: etree.Element,
        schema_path: Path
    ) -> Dict[str, str]:
        """
        Extract extension namespace from schema.
        
        Args:
            root: Schema root element
            schema_path: Path to schema file
            
        Returns:
            Dictionary with namespace info
        """
        # Get target namespace attribute
        target_ns = root.get('targetNamespace')
        
        if not target_ns:
            raise ValueError("Schema missing targetNamespace attribute")
        
        # Find namespace prefix from document
        prefix = None
        for ns_prefix, ns_uri in root.nsmap.items():
            if ns_uri == target_ns and ns_prefix:
                prefix = ns_prefix
                break
        
        # If no prefix found, extract from filename
        if not prefix:
            filename = schema_path.stem
            if '-' in filename:
                prefix = filename.split('-')[0]
        
        # Extract year from filename (company-YYYY.xsd)
        year = None
        filename = schema_path.stem
        if '-' in filename:
            parts = filename.split('-')
            if len(parts) > 1 and parts[1].isdigit():
                year = parts[1]
        
        return {
            'namespace': target_ns,
            'prefix': prefix,
            'year': year
        }
    
    def _extract_elements(
        self,
        root: etree.Element,
        target_namespace: str
    ) -> List[Dict[str, any]]:
        """
        Extract element definitions from schema.
        
        Args:
            root: Schema root element
            target_namespace: Target namespace URI
            
        Returns:
            List of element definitions
        """
        elements = []
        
        # Find all element definitions
        for elem in root.findall('.//xsd:element', self.NAMESPACES):
            element_data = self._parse_element(elem, target_namespace)
            if element_data:
                elements.append(element_data)
        
        return elements
    
    def _parse_element(
        self,
        elem: etree.Element,
        target_namespace: str
    ) -> Optional[Dict[str, any]]:
        """
        Parse individual element definition.
        
        Args:
            elem: Element XML element
            target_namespace: Target namespace URI
            
        Returns:
            Element definition dictionary or None
        """
        name = elem.get('name')
        if not name:
            return None
        
        element_data = {
            'name': name,
            'type': elem.get('type'),
            'substitution_group': elem.get('substitutionGroup'),
            'abstract': elem.get('abstract') == 'true',
            'nillable': elem.get('nillable') == 'true',
            'id': elem.get('id'),
        }
        
        # Parse period type if present
        period_type = elem.get(
            '{http://www.xbrl.org/2003/instance}periodType'
        )
        if period_type:
            element_data['period_type'] = period_type
        
        # Parse balance type if present
        balance = elem.get(
            '{http://www.xbrl.org/2003/instance}balance'
        )
        if balance:
            element_data['balance'] = balance
        
        return element_data
    
    def _extract_imports(self, root: etree.Element) -> List[Dict[str, str]]:
        """
        Extract schema imports.
        
        Args:
            root: Schema root element
            
        Returns:
            List of import information
        """
        imports = []
        
        # Find import elements
        for imp in root.findall('.//xsd:import', self.NAMESPACES):
            namespace = imp.get('namespace')
            schema_location = imp.get('schemaLocation')
            
            if namespace:
                imports.append({
                    'namespace': namespace,
                    'schema_location': schema_location
                })
        
        return imports
    
    def get_element_names(self, parsed_schema: Dict[str, any]) -> Set[str]:
        """
        Get set of element names from parsed schema.
        
        Args:
            parsed_schema: Result from parse()
            
        Returns:
            Set of element names
        """
        return {elem['name'] for elem in parsed_schema.get('elements', [])}
    
    def get_elements_by_type(
        self,
        parsed_schema: Dict[str, any],
        element_type: str
    ) -> List[Dict[str, any]]:
        """
        Filter elements by type.
        
        Args:
            parsed_schema: Result from parse()
            element_type: Type to filter by
            
        Returns:
            List of matching elements
        """
        return [
            elem for elem in parsed_schema.get('elements', [])
            if elem.get('type') == element_type
        ]
    
    def get_monetary_elements(
        self,
        parsed_schema: Dict[str, any]
    ) -> List[Dict[str, any]]:
        """
        Get monetary elements from schema.
        
        Args:
            parsed_schema: Result from parse()
            
        Returns:
            List of monetary elements
        """
        monetary_types = [
            'xbrli:monetaryItemType',
            'monetaryItemType',
            'monetary'
        ]
        
        return [
            elem for elem in parsed_schema.get('elements', [])
            if any(mt in str(elem.get('type', '')) for mt in monetary_types)
        ]