"""
Schema Analyzer
===============

Analyzes XBRL schema (.xsd) files to extract structure and metadata.

Schemas define elements, imports, and references to linkbases.
This module parses schemas to understand taxonomy organization.

Classes:
    SchemaAnalyzer: Analyzes XSD schema files
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import xml.etree.ElementTree as ET


class SchemaAnalyzer:
    """
    Analyzes XBRL schema files to extract structure.
    
    Schemas contain:
    - Element definitions (concepts)
    - Import statements (references to other taxonomies)
    - Linkbase references (pointers to presentation, calculation, etc.)
    - Namespace declarations
    - Role type definitions
    """
    
    # Standard XML namespaces
    NAMESPACES = {
        'xsd': 'http://www.w3.org/2001/XMLSchema',
        'link': 'http://www.xbrl.org/2003/linkbase',
        'xlink': 'http://www.w3.org/1999/xlink',
        'xbrli': 'http://www.xbrl.org/2003/instance',
    }
    
    # Linkbase types
    LINKBASE_TYPES = {
        'presentationLinkbaseRef': 'presentation',
        'calculationLinkbaseRef': 'calculation',
        'definitionLinkbaseRef': 'definition',
        'labelLinkbaseRef': 'label',
        'referenceLinkbaseRef': 'reference',
    }
    
    def __init__(self):
        """Initialize schema analyzer."""
        pass
    
    def analyze(self, schema_path: Path) -> Dict[str, any]:
        """
        Analyze a schema file and extract all information.
        
        Args:
            schema_path: Path to .xsd schema file
            
        Returns:
            Dictionary containing:
            {
                'namespaces': {'prefix': 'uri', ...},
                'imports': ['path1', 'path2', ...],
                'linkbase_refs': {
                    'presentation': ['file1.xml', ...],
                    'calculation': [...],
                    ...
                },
                'target_namespace': 'http://...',
                'element_form_default': 'qualified',
            }
            
        Raises:
            FileNotFoundError: If schema file doesn't exist
        """
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        result = {
            'namespaces': {},
            'imports': [],
            'linkbase_refs': {
                'presentation': [],
                'calculation': [],
                'definition': [],
                'label': [],
                'reference': [],
            },
            'target_namespace': None,
            'element_form_default': None,
        }
        
        try:
            tree = ET.parse(schema_path)
            root = tree.getroot()
            
            # Extract namespaces
            result['namespaces'] = self._extract_namespaces(root)
            
            # Extract target namespace
            result['target_namespace'] = root.get('targetNamespace')
            
            # Extract elementFormDefault
            result['element_form_default'] = root.get('elementFormDefault')
            
            # Extract imports
            result['imports'] = self._extract_imports(root, schema_path)
            
            # Extract linkbase references
            result['linkbase_refs'] = self._extract_linkbase_refs(root, schema_path)
            
        except ET.ParseError:
            # Return partial result if parsing fails
            pass
        
        return result
    
    def _extract_namespaces(self, root: ET.Element) -> Dict[str, str]:
        """
        Extract all namespace declarations from schema.
        
        Args:
            root: Root XML element
            
        Returns:
            Dictionary mapping prefixes to namespace URIs
        """
        namespaces = {}
        
        # Extract from root element attributes
        for key, value in root.attrib.items():
            if key.startswith('{http://www.w3.org/2000/xmlns/}'):
                # Namespace declaration: xmlns:prefix="uri"
                prefix = key.split('}')[1]
                namespaces[prefix] = value
            elif key == 'xmlns':
                # Default namespace
                namespaces[''] = value
        
        return namespaces
    
    def _extract_imports(
        self,
        root: ET.Element,
        schema_path: Path
    ) -> List[str]:
        """
        Extract import statements from schema.
        
        Imports reference other schema files that this schema depends on.
        
        Args:
            root: Root XML element
            schema_path: Path to current schema (for resolving relative paths)
            
        Returns:
            List of imported schema locations
        """
        imports = []
        
        for import_elem in root.findall('.//xsd:import', self.NAMESPACES):
            schema_location = import_elem.get('schemaLocation')
            
            if schema_location:
                # Resolve relative to current schema
                if not schema_location.startswith('http'):
                    # Relative path
                    resolved = (schema_path.parent / schema_location).resolve()
                    imports.append(str(resolved))
                else:
                    # Absolute URI
                    imports.append(schema_location)
        
        return imports
    
    def _extract_linkbase_refs(
        self,
        root: ET.Element,
        schema_path: Path
    ) -> Dict[str, List[str]]:
        """
        Extract linkbase references from schema annotations.
        
        Schemas reference linkbase files through linkbaseRef elements
        in appinfo annotations.
        
        Args:
            root: Root XML element
            schema_path: Path to current schema
            
        Returns:
            Dictionary mapping linkbase types to file paths
        """
        linkbase_refs = {
            'presentation': [],
            'calculation': [],
            'definition': [],
            'label': [],
            'reference': [],
        }
        
        # Find all linkbaseRef elements
        for linkbase_ref in root.findall('.//link:linkbaseRef', self.NAMESPACES):
            # Get the role to determine type
            role = linkbase_ref.get('{http://www.w3.org/1999/xlink}role', '')
            href = linkbase_ref.get('{http://www.w3.org/1999/xlink}href', '')
            
            if not href:
                continue
            
            # Classify linkbase type by role
            linkbase_type = self._classify_linkbase_type(role)
            
            if linkbase_type:
                # Resolve relative path
                if not href.startswith('http'):
                    resolved = (schema_path.parent / href).resolve()
                    linkbase_refs[linkbase_type].append(str(resolved))
                else:
                    linkbase_refs[linkbase_type].append(href)
        
        return linkbase_refs
    
    def _classify_linkbase_type(self, role: str) -> Optional[str]:
        """
        Classify linkbase type from role URI.
        
        Args:
            role: Role URI from linkbaseRef
            
        Returns:
            Linkbase type ('presentation', 'calculation', etc.) or None
        """
        for ref_type, linkbase_type in self.LINKBASE_TYPES.items():
            if ref_type in role:
                return linkbase_type
        
        return None
    
    def find_entry_point_schema(self, taxonomy_path: Path) -> Optional[Path]:
        """
        Find the main entry point schema file.
        
        Searches for the primary schema file that defines the taxonomy.
        Common patterns:
        - {taxonomy-name}.xsd (e.g., us-gaap-2025.xsd)
        - {taxonomy-name}-{version}.xsd
        - taxonomy.xsd
        
        Args:
            taxonomy_path: Root taxonomy directory
            
        Returns:
            Path to entry point schema or None if not found
        """
        # Try common patterns based on directory name
        taxonomy_name = taxonomy_path.name
        
        candidates = [
            taxonomy_path / f"{taxonomy_name}.xsd",
            taxonomy_path / "taxonomy.xsd",
            taxonomy_path / "main.xsd",
        ]
        
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate
        
        # Find largest .xsd file in root (often the entry point)
        xsd_files = list(taxonomy_path.glob('*.xsd'))
        if xsd_files:
            # Return largest file (entry points are typically comprehensive)
            return max(xsd_files, key=lambda p: p.stat().st_size)
        
        return None
    
    def analyze_multiple(self, schema_paths: List[Path]) -> Dict[Path, Dict[str, any]]:
        """
        Analyze multiple schema files.
        
        Args:
            schema_paths: List of schema file paths
            
        Returns:
            Dictionary mapping schema paths to analysis results
        """
        results = {}
        
        for schema_path in schema_paths:
            try:
                results[schema_path] = self.analyze(schema_path)
            except FileNotFoundError:
                # Skip missing files
                continue
        
        return results
    
    def get_all_linkbases(
        self,
        analyses: Dict[Path, Dict[str, any]]
    ) -> Dict[str, Set[str]]:
        """
        Aggregate all linkbase references from multiple analyses.
        
        Args:
            analyses: Dictionary of analysis results from analyze_multiple()
            
        Returns:
            Dictionary mapping linkbase types to sets of file paths
        """
        aggregated = {
            'presentation': set(),
            'calculation': set(),
            'definition': set(),
            'label': set(),
            'reference': set(),
        }
        
        for analysis in analyses.values():
            linkbase_refs = analysis.get('linkbase_refs', {})
            
            for linkbase_type, files in linkbase_refs.items():
                aggregated[linkbase_type].update(files)
        
        return aggregated