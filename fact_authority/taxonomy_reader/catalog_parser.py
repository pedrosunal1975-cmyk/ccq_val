"""
Catalog Parser
==============

Parses XBRL catalog.xml files to extract namespace mappings.

The catalog file maps namespace URIs to physical file locations,
enabling taxonomy resolution. This is standard XBRL infrastructure.

Classes:
    CatalogParser: Parser for catalog.xml files
"""

from pathlib import Path
from typing import Dict, Optional
import xml.etree.ElementTree as ET


class CatalogParser:
    """
    Parser for XBRL catalog.xml files.
    
    Catalog files provide namespace resolution, mapping URIs to files.
    This is essential for understanding how a taxonomy is organized.
    
    Example catalog.xml:
        <catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
          <rewriteURI uriStartString="http://fasb.org/us-gaap/2025"
                       rewritePrefix="./elts/"/>
        </catalog>
    """
    
    # Standard catalog namespace
    CATALOG_NS = 'urn:oasis:names:tc:entity:xmlns:xml:catalog'
    
    def __init__(self):
        """Initialize catalog parser."""
        self.namespaces = {'cat': self.CATALOG_NS}
    
    def parse(self, catalog_path: Path) -> Dict[str, str]:
        """
        Parse catalog.xml file.
        
        Args:
            catalog_path: Path to catalog.xml file
            
        Returns:
            Dictionary mapping namespace URIs to file path prefixes
            
        Raises:
            FileNotFoundError: If catalog file doesn't exist
            ET.ParseError: If XML is malformed
        """
        if not catalog_path.exists():
            raise FileNotFoundError(f"Catalog file not found: {catalog_path}")
        
        mappings = {}
        
        try:
            tree = ET.parse(catalog_path)
            root = tree.getroot()
            
            # Extract rewriteURI mappings
            mappings.update(self._extract_rewrite_uri(root))
            
            # Extract uri mappings
            mappings.update(self._extract_uri_mappings(root))
            
            # Extract system mappings (less common)
            mappings.update(self._extract_system_mappings(root))
            
        except ET.ParseError as e:
            # If parsing fails, return empty dict (non-fatal)
            # Some taxonomies may not have catalog files
            return {}
        
        return mappings
    
    def _extract_rewrite_uri(self, root: ET.Element) -> Dict[str, str]:
        """
        Extract rewriteURI elements from catalog.
        
        rewriteURI maps a URI prefix to a file path prefix:
        <rewriteURI uriStartString="http://example.com/taxonomy"
                     rewritePrefix="./files/"/>
        
        Args:
            root: Root XML element
            
        Returns:
            Dictionary of URI mappings
        """
        mappings = {}
        
        # Try with namespace
        for elem in root.findall('.//cat:rewriteURI', self.namespaces):
            uri_start = elem.get('uriStartString')
            rewrite_prefix = elem.get('rewritePrefix')
            
            if uri_start and rewrite_prefix:
                mappings[uri_start] = rewrite_prefix
        
        # Try without namespace (some catalogs omit it)
        for elem in root.findall('.//rewriteURI'):
            uri_start = elem.get('uriStartString')
            rewrite_prefix = elem.get('rewritePrefix')
            
            if uri_start and rewrite_prefix:
                mappings[uri_start] = rewrite_prefix
        
        return mappings
    
    def _extract_uri_mappings(self, root: ET.Element) -> Dict[str, str]:
        """
        Extract uri elements from catalog.
        
        uri elements provide direct URI to file mappings:
        <uri name="http://example.com/schema.xsd"
             uri="./schema.xsd"/>
        
        Args:
            root: Root XML element
            
        Returns:
            Dictionary of URI mappings
        """
        mappings = {}
        
        # Try with namespace
        for elem in root.findall('.//cat:uri', self.namespaces):
            name = elem.get('name')
            uri = elem.get('uri')
            
            if name and uri:
                mappings[name] = uri
        
        # Try without namespace
        for elem in root.findall('.//uri'):
            name = elem.get('name')
            uri = elem.get('uri')
            
            if name and uri:
                mappings[name] = uri
        
        return mappings
    
    def _extract_system_mappings(self, root: ET.Element) -> Dict[str, str]:
        """
        Extract system mappings from catalog.
        
        system elements map system identifiers to files:
        <system systemId="http://example.com/schema.xsd"
                uri="./schema.xsd"/>
        
        Args:
            root: Root XML element
            
        Returns:
            Dictionary of system mappings
        """
        mappings = {}
        
        # Try with namespace
        for elem in root.findall('.//cat:system', self.namespaces):
            system_id = elem.get('systemId')
            uri = elem.get('uri')
            
            if system_id and uri:
                mappings[system_id] = uri
        
        # Try without namespace
        for elem in root.findall('.//system'):
            system_id = elem.get('systemId')
            uri = elem.get('uri')
            
            if system_id and uri:
                mappings[system_id] = uri
        
        return mappings
    
    def find_catalog_file(self, taxonomy_path: Path) -> Optional[Path]:
        """
        Find catalog.xml file in taxonomy directory.
        
        Searches for catalog file in standard locations:
        - catalog.xml (root)
        - META-INF/catalog.xml (standard location)
        - taxonomies/catalog.xml
        
        Args:
            taxonomy_path: Root taxonomy directory
            
        Returns:
            Path to catalog file or None if not found
        """
        # Common catalog locations
        candidates = [
            taxonomy_path / 'catalog.xml',
            taxonomy_path / 'META-INF' / 'catalog.xml',
            taxonomy_path / 'taxonomies' / 'catalog.xml',
        ]
        
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate
        
        # Search recursively (up to 2 levels deep)
        for catalog in taxonomy_path.rglob('catalog.xml'):
            # Limit depth to avoid performance issues
            depth = len(catalog.relative_to(taxonomy_path).parts)
            if depth <= 2:
                return catalog
        
        return None
    
    def resolve_uri(
        self,
        uri: str,
        mappings: Dict[str, str],
        base_path: Path
    ) -> Optional[Path]:
        """
        Resolve a URI to a file path using catalog mappings.
        
        Args:
            uri: URI to resolve
            mappings: Catalog mappings from parse()
            base_path: Base path for relative paths
            
        Returns:
            Resolved file path or None if cannot resolve
        """
        # Direct mapping
        if uri in mappings:
            relative_path = mappings[uri]
            return base_path / relative_path
        
        # Prefix mapping (rewriteURI)
        for uri_prefix, path_prefix in mappings.items():
            if uri.startswith(uri_prefix):
                # Replace URI prefix with path prefix
                relative_part = uri[len(uri_prefix):]
                return base_path / path_prefix / relative_part
        
        return None