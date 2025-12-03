"""
Taxonomy Reader
===============

Main orchestrator for understanding XBRL taxonomies.

This is the "learn the language before reading the book" engine.
It reads a taxonomy's self-documenting files to understand its
structure, roles, and organization.

Classes:
    TaxonomyReader: Main taxonomy understanding engine
"""

from pathlib import Path
from typing import Dict, List, Optional
import logging

from engines.fact_authority.taxonomy_reader.taxonomy_profile import TaxonomyProfile
from engines.fact_authority.taxonomy_reader.catalog_parser import CatalogParser
from engines.fact_authority.taxonomy_reader.schema_analyzer import SchemaAnalyzer
from engines.fact_authority.taxonomy_reader.role_extractor import RoleExtractor
from engines.fact_authority.taxonomy_reader.element_property_extractor import ElementPropertyExtractor
from engines.fact_authority.taxonomy_reader.calculation_parser import CalculationParser
from engines.fact_authority.taxonomy_reader.definition_parser import DefinitionParser
from engines.fact_authority.taxonomy_reader.label_parser import LabelParser


logger = logging.getLogger(__name__)


class TaxonomyReader:
    """
    Reads and understands XBRL taxonomies.
    
    This is the core of the taxonomy_reader sub-engine. It orchestrates
    the parsing of catalog files, schema files, and linkbase files to
    build a complete understanding of a taxonomy's structure.
    
    Usage:
        reader = TaxonomyReader()
        profile = reader.read_taxonomy(Path('/taxonomies/libraries/us-gaap-2025'))
        
        # Now we understand the taxonomy
        print(profile.metadata['name'])  # 'us-gaap'
        print(profile.roles.keys())      # All statement roles
    """
    
    def __init__(self):
        """Initialize taxonomy reader."""
        self.catalog_parser = CatalogParser()
        self.schema_analyzer = SchemaAnalyzer()
        self.role_extractor = RoleExtractor()
        self.element_extractor = ElementPropertyExtractor()
        self.calculation_parser = CalculationParser()
        self.definition_parser = DefinitionParser()
        self.label_parser = LabelParser()
    
    def read_taxonomy(self, taxonomy_paths: List[Path]) -> TaxonomyProfile:
        """
        Read and understand a taxonomy.
        
        This is the main entry point. It analyzes all taxonomy files
        to build a complete understanding of the taxonomy's structure.
        
        Args:
            taxonomy_paths: List of taxonomy directory paths
            
        Returns:
            TaxonomyProfile with complete taxonomy understanding
            
        Raises:
            FileNotFoundError: If taxonomy path doesn't exist
            ValueError: If taxonomy cannot be understood
        """
        # Use first path as primary taxonomy
        taxonomy_path = taxonomy_paths[0] if isinstance(taxonomy_paths, list) else taxonomy_paths
        
        if not taxonomy_path.exists():
            raise FileNotFoundError(f"Taxonomy path not found: {taxonomy_path}")
        
        if not taxonomy_path.is_dir():
            raise ValueError(f"Taxonomy path must be a directory: {taxonomy_path}")
        
        logger.info(f"Reading taxonomy: {taxonomy_path}")
        
        # Initialize profile
        profile = TaxonomyProfile()
        
        # Step 1: Extract basic metadata
        profile.metadata = self._extract_metadata(taxonomy_path)
        logger.info(f"Taxonomy: {profile.metadata.get('name', 'unknown')}")
        
        # Step 2: Discover all files
        structure = self._discover_structure(taxonomy_path)
        profile.structure = structure
        logger.info(
            f"Found {len(structure.get('schema_files', []))} schemas, "
            f"{len(structure.get('linkbases', {}).get('presentation', []))} presentation linkbases"
        )
        
        # Step 3: Parse catalog (if exists)
        catalog_mappings = self._parse_catalog(structure.get('catalog_file'))
        
        # Step 4: Analyze schemas
        schema_info = self._analyze_schemas(structure.get('schema_files', []))
        
        # Step 5: Extract namespaces
        profile.namespaces = self._extract_namespaces(schema_info)
        logger.info(f"Found {len(profile.namespaces)} namespaces")
        
        # Step 6: Extract roles
        profile.roles = self._extract_roles(structure.get('schema_files', []))
        logger.info(f"Found {len(profile.roles)} statement roles")
        
        # Step 7: Extract element properties (Phase 2)
        profile.elements = self._extract_elements(structure.get('schema_files', []))
        logger.info(f"Found {len(profile.elements)} element properties")
        
        # Step 8: Parse calculation relationships (Phase 2)
        calc_linkbases = structure.get('linkbases', {}).get('calculation', [])
        profile.calculations = self._parse_calculations(calc_linkbases)
        logger.info(f"Found {len(profile.calculations)} calculation roles")
        
        # Step 9: Parse dimensional relationships (Phase 2)
        def_linkbases = structure.get('linkbases', {}).get('definition', [])
        profile.dimensions = self._parse_dimensions(def_linkbases)
        axes_count = len(profile.dimensions.get('axes', {}))
        hypercubes_count = len(profile.dimensions.get('hypercubes', {}))
        logger.info(f"Found {axes_count} axes and {hypercubes_count} hypercubes")
        
        # Step 10: Parse labels (Phase 2)
        label_linkbases = structure.get('linkbases', {}).get('label', [])
        profile.labels = self._parse_labels(label_linkbases)
        logger.info(f"Found labels for {len(profile.labels)} concepts")
        
        return profile
    
    def _extract_metadata(self, taxonomy_path: Path) -> Dict[str, str]:
        """
        Extract basic metadata from taxonomy path.
        
        Args:
            taxonomy_path: Taxonomy directory path
            
        Returns:
            Dictionary with name, version, and other metadata
        """
        # Parse taxonomy name and version from directory name
        # Common patterns: us-gaap-2025, ifrs-2024, dei-2024
        name_parts = taxonomy_path.name.split('-')
        
        if len(name_parts) >= 2:
            # Last part is usually version
            version = name_parts[-1]
            name = '-'.join(name_parts[:-1])
        else:
            name = taxonomy_path.name
            version = 'unknown'
        
        return {
            'name': name,
            'version': version,
            'path': str(taxonomy_path),
        }
    
    def _discover_structure(self, taxonomy_path: Path) -> Dict[str, any]:
        """
        Discover all taxonomy files.
        
        Args:
            taxonomy_path: Taxonomy directory path
            
        Returns:
            Dictionary with file structure
        """
        structure = {}
        
        # Find catalog file
        catalog_file = self.catalog_parser.find_catalog_file(taxonomy_path)
        structure['catalog_file'] = catalog_file
        
        # Find entry point schema
        entry_point = self.schema_analyzer.find_entry_point_schema(taxonomy_path)
        structure['entry_point'] = entry_point
        
        # Find all schema files
        schema_files = list(taxonomy_path.rglob('*.xsd'))
        structure['schema_files'] = schema_files
        
        # Find all linkbases using file discoverer
        structure['linkbases'] = {
            'presentation': list(taxonomy_path.glob('*_pre.xml')),
            'calculation': list(taxonomy_path.glob('*_cal.xml')),
            'definition': list(taxonomy_path.glob('*_def.xml')),
            'label': list(taxonomy_path.glob('*_lab.xml')),
        }
        
        return structure
    
    def _parse_catalog(self, catalog_file: Optional[Path]) -> Dict[str, str]:
        """
        Parse catalog file if it exists.
        
        Args:
            catalog_file: Path to catalog.xml or None
            
        Returns:
            Catalog mappings or empty dict
        """
        if not catalog_file:
            return {}
        
        try:
            return self.catalog_parser.parse(catalog_file)
        except Exception as e:
            logger.warning(f"Failed to parse catalog: {e}")
            return {}
    
    def _analyze_schemas(self, schema_files: List[Path]) -> Dict[Path, Dict[str, any]]:
        """
        Analyze all schema files.
        
        Args:
            schema_files: List of schema file paths
            
        Returns:
            Dictionary mapping schema paths to analysis results
        """
        return self.schema_analyzer.analyze_multiple(schema_files)
    
    def _extract_namespaces(
        self,
        schema_info: Dict[Path, Dict[str, any]]
    ) -> Dict[str, str]:
        """
        Extract all namespaces from schema analyses.
        
        Args:
            schema_info: Schema analysis results
            
        Returns:
            Dictionary mapping prefixes to namespace URIs
        """
        namespaces = {}
        
        for analysis in schema_info.values():
            # Add namespaces from this schema
            namespaces.update(analysis.get('namespaces', {}))
            
            # Add target namespace
            target_ns = analysis.get('target_namespace')
            if target_ns:
                # Try to extract prefix from target namespace URI
                # e.g., http://fasb.org/us-gaap/2025 -> us-gaap
                parts = target_ns.rstrip('/').split('/')
                if len(parts) >= 2:
                    prefix = parts[-2]  # Second to last part
                    namespaces[prefix] = target_ns
        
        return namespaces
    
    def _extract_roles(self, schema_files: List[Path]) -> Dict[str, Dict[str, any]]:
        """
        Extract all role definitions from schemas.
        
        Args:
            schema_files: List of schema file paths
            
        Returns:
            Dictionary mapping role URIs to role information
        """
        return self.role_extractor.extract_from_multiple_files(schema_files)
    
    def _extract_elements(self, schema_files: List[Path]) -> Dict[str, Dict[str, any]]:
        """
        Extract all element properties from schemas.
        
        Args:
            schema_files: List of schema file paths
            
        Returns:
            Dictionary mapping concept QNames to element properties
        """
        return self.element_extractor.extract_from_multiple_schemas(schema_files)
    
    def _parse_calculations(
        self,
        calc_linkbases: List[Path]
    ) -> Dict[str, Dict[str, Dict[str, any]]]:
        """
        Parse all calculation relationships from linkbases.
        
        Args:
            calc_linkbases: List of calculation linkbase file paths
            
        Returns:
            Dictionary mapping role URIs to calculation relationships
        """
        return self.calculation_parser.parse_multiple(calc_linkbases)
    
    def _parse_dimensions(self, def_linkbases: List[Path]) -> Dict[str, any]:
        """
        Parse all dimensional relationships from linkbases.
        
        Args:
            def_linkbases: List of definition linkbase file paths
            
        Returns:
            Dictionary containing axes and hypercubes
        """
        return self.definition_parser.parse_multiple(def_linkbases)
    
    def _parse_labels(
        self,
        label_linkbases: List[Path]
    ) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Parse all labels from linkbases.
        
        Args:
            label_linkbases: List of label linkbase file paths
            
        Returns:
            Dictionary mapping concepts to labels
        """
        return self.label_parser.parse_multiple(label_linkbases)
    
    def get_statement_types(self, profile: TaxonomyProfile) -> List[str]:
        """
        Get list of statement types defined in taxonomy.
        
        Args:
            profile: Taxonomy profile
            
        Returns:
            List of unique statement types (e.g., ['balance_sheet', 'income_statement'])
        """
        statement_types = set()
        
        for role_info in profile.roles.values():
            stmt_type = role_info.get('type')
            if stmt_type and stmt_type != 'other':
                statement_types.add(stmt_type)
        
        return sorted(statement_types)
    
    def get_roles_for_statement(
        self,
        profile: TaxonomyProfile,
        statement_type: str
    ) -> List[str]:
        """
        Get all role URIs for a specific statement type.
        
        Args:
            profile: Taxonomy profile
            statement_type: Statement type (e.g., 'balance_sheet')
            
        Returns:
            List of role URIs
        """
        return [
            uri
            for uri, info in profile.roles.items()
            if info.get('type') == statement_type
        ]