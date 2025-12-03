"""
Taxonomy Profile
================

Data structure for storing complete taxonomy understanding.

This module defines the TaxonomyProfile class which represents
a taxonomy's complete structure, roles, namespaces, and metadata
after being analyzed by the taxonomy_reader sub-engine.

Classes:
    TaxonomyProfile: Complete taxonomy understanding data structure
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class TaxonomyProfile:
    """
    Complete understanding of a taxonomy's structure.
    
    This is the output of the taxonomy_reader sub-engine.
    It represents everything we learned about a taxonomy by
    reading its self-documenting files (catalog, schemas, linkbases).
    
    Attributes:
        metadata: Basic taxonomy information (name, version, namespace)
        structure: File locations and organization
        namespaces: All namespaces defined in this taxonomy
        roles: All statement roles defined (balance sheet, income, etc.)
        format_version: Profile format version (for cache invalidation)
        generated_at: When this profile was created
    """
    
    # Basic metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    
    # File structure
    structure: Dict[str, any] = field(default_factory=dict)
    
    # Namespace mappings
    namespaces: Dict[str, str] = field(default_factory=dict)
    
    # Role definitions (statement types)
    roles: Dict[str, Dict[str, any]] = field(default_factory=dict)
    
    # Element properties (Phase 2)
    elements: Dict[str, Dict[str, any]] = field(default_factory=dict)
    
    # Calculation relationships (Phase 2)
    calculations: Dict[str, Dict[str, Dict[str, any]]] = field(default_factory=dict)
    
    # Dimensional relationships (Phase 2)
    dimensions: Dict[str, any] = field(default_factory=dict)
    
    # Labels (Phase 2)
    labels: Dict[str, Dict[str, Dict[str, str]]] = field(default_factory=dict)
    
    # Version control
    format_version: str = '1.0'
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict:
        """
        Convert profile to dictionary.
        
        Returns:
            Dictionary representation of the profile
        """
        return {
            'metadata': self.metadata,
            'structure': self._structure_to_dict(),
            'namespaces': self.namespaces,
            'roles': self.roles,
            'elements': self.elements,
            'calculations': self.calculations,
            'dimensions': self.dimensions,
            'labels': self.labels,
            'format_version': self.format_version,
            'generated_at': self.generated_at
        }
    
    def _structure_to_dict(self) -> dict:
        """
        Convert structure paths to strings for JSON serialization.
        
        Returns:
            Structure dictionary with string paths
        """
        result = {}
        
        for key, value in self.structure.items():
            if isinstance(value, Path):
                result[key] = str(value)
            elif isinstance(value, list):
                result[key] = [str(p) if isinstance(p, Path) else p for p in value]
            elif isinstance(value, dict):
                result[key] = {
                    k: [str(p) if isinstance(p, Path) else p for p in v]
                    if isinstance(v, list) else str(v) if isinstance(v, Path) else v
                    for k, v in value.items()
                }
            else:
                result[key] = value
        
        return result
    
    def to_json(self, filepath: Path):
        """
        Save profile to JSON file.
        
        Args:
            filepath: Path to save JSON file
        """
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TaxonomyProfile':
        """
        Create profile from dictionary.
        
        Args:
            data: Dictionary with profile data
            
        Returns:
            TaxonomyProfile instance
        """
        profile = cls()
        profile.metadata = data.get('metadata', {})
        profile.structure = cls._structure_from_dict(data.get('structure', {}))
        profile.namespaces = data.get('namespaces', {})
        profile.roles = data.get('roles', {})
        profile.elements = data.get('elements', {})
        profile.calculations = data.get('calculations', {})
        profile.dimensions = data.get('dimensions', {})
        profile.labels = data.get('labels', {})
        profile.format_version = data.get('format_version', '1.0')
        profile.generated_at = data.get('generated_at', '')
        
        return profile
    
    @classmethod
    def _structure_from_dict(cls, data: dict) -> dict:
        """
        Convert structure strings back to Paths.
        
        Args:
            data: Structure dictionary with string paths
            
        Returns:
            Structure dictionary with Path objects
        """
        result = {}
        
        for key, value in data.items():
            if key == 'catalog_file' or key == 'entry_point':
                result[key] = Path(value) if value else None
            elif key == 'schema_files':
                result[key] = [Path(p) for p in value] if value else []
            elif key == 'linkbases' and isinstance(value, dict):
                result[key] = {
                    k: [Path(p) for p in v] if isinstance(v, list) else v
                    for k, v in value.items()
                }
            else:
                result[key] = value
        
        return result
    
    @classmethod
    def from_json(cls, filepath: Path) -> 'TaxonomyProfile':
        """
        Load profile from JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            TaxonomyProfile instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is invalid JSON
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    def get_statement_roles(self) -> Dict[str, str]:
        """
        Get mapping of role URIs to statement types.
        
        Returns:
            Dictionary mapping role URI to statement type
            (e.g., 'http://fasb.org/.../StatementOfFinancialPosition' -> 'balance_sheet')
        """
        return {
            uri: role_info['type']
            for uri, role_info in self.roles.items()
            if 'type' in role_info
        }
    
    def get_namespace_for_prefix(self, prefix: str) -> Optional[str]:
        """
        Get namespace URI for a prefix.
        
        Args:
            prefix: Namespace prefix (e.g., 'us-gaap')
            
        Returns:
            Namespace URI or None if not found
        """
        return self.namespaces.get(prefix)
    
    def get_presentation_linkbases(self) -> List[Path]:
        """
        Get all presentation linkbase files.
        
        Returns:
            List of presentation linkbase paths
        """
        linkbases = self.structure.get('linkbases', {})
        return linkbases.get('presentation', [])
    
    def get_calculation_linkbases(self) -> List[Path]:
        """
        Get all calculation linkbase files.
        
        Returns:
            List of calculation linkbase paths
        """
        linkbases = self.structure.get('linkbases', {})
        return linkbases.get('calculation', [])
    
    def get_definition_linkbases(self) -> List[Path]:
        """
        Get all definition linkbase files.
        
        Returns:
            List of definition linkbase paths
        """
        linkbases = self.structure.get('linkbases', {})
        return linkbases.get('definition', [])
    
    def get_label_linkbases(self) -> List[Path]:
        """
        Get all label linkbase files.
        
        Returns:
            List of label linkbase paths
        """
        linkbases = self.structure.get('linkbases', {})
        return linkbases.get('label', [])
    
    def get_schema_files(self) -> List[Path]:
        """
        Get all schema files.
        
        Returns:
            List of schema file paths
        """
        return self.structure.get('schema_files', [])
    
    def get_element_property(self, concept: str, property_name: str) -> any:
        """
        Get a specific property for an element.
        
        Args:
            concept: Concept QName (e.g., 'us-gaap:Cash')
            property_name: Property to retrieve (e.g., 'period_type', 'balance')
            
        Returns:
            Property value or None if not found
        """
        element = self.elements.get(concept, {})
        return element.get(property_name)
    
    def get_elements_by_type(self, base_type: str) -> Dict[str, Dict[str, any]]:
        """
        Get all elements of a specific base type.
        
        Args:
            base_type: Base type ('monetary', 'shares', 'numeric', etc.)
            
        Returns:
            Dictionary of matching elements
        """
        return {
            qname: props
            for qname, props in self.elements.items()
            if props.get('base_type') == base_type
        }
    
    def get_abstract_elements(self) -> Dict[str, Dict[str, any]]:
        """
        Get all abstract elements (headers/groupings).
        
        Returns:
            Dictionary of abstract elements
        """
        return {
            qname: props
            for qname, props in self.elements.items()
            if props.get('abstract', False)
        }
    
    def get_concrete_elements(self) -> Dict[str, Dict[str, any]]:
        """
        Get all concrete elements (actual data concepts).
        
        Returns:
            Dictionary of concrete elements
        """
        return {
            qname: props
            for qname, props in self.elements.items()
            if not props.get('abstract', False)
        }
    
    def get_calculations_for_role(self, role: str) -> Dict[str, Dict[str, any]]:
        """
        Get all calculation relationships for a specific role.
        
        Args:
            role: Role URI (e.g., 'http://fasb.org/.../BalanceSheet')
            
        Returns:
            Dictionary of parent concepts and their children
        """
        return self.calculations.get(role, {})
    
    def get_calculation_children(
        self,
        role: str,
        parent_concept: str
    ) -> List[Dict[str, any]]:
        """
        Get children for a specific calculation.
        
        Args:
            role: Role URI
            parent_concept: Parent concept QName
            
        Returns:
            List of child dictionaries with concept, weight, order
        """
        role_calcs = self.calculations.get(role, {})
        parent_data = role_calcs.get(parent_concept, {})
        return parent_data.get('children', [])
    
    def get_axes(self) -> Dict[str, Dict[str, any]]:
        """
        Get all axes (dimensions).
        
        Returns:
            Dictionary of axes with their domains and members
        """
        return self.dimensions.get('axes', {})
    
    def get_axis_members(self, axis: str) -> List[str]:
        """
        Get members for a specific axis.
        
        Args:
            axis: Axis QName (e.g., 'us-gaap:StatementGeographicalAxis')
            
        Returns:
            List of member QNames
        """
        axes = self.dimensions.get('axes', {})
        axis_data = axes.get(axis, {})
        return axis_data.get('members', [])
    
    def get_hypercubes(self) -> Dict[str, Dict[str, any]]:
        """
        Get all hypercubes (dimensional tables).
        
        Returns:
            Dictionary of hypercubes with their dimensions and primary items
        """
        return self.dimensions.get('hypercubes', {})
    
    def get_label(
        self,
        concept: str,
        label_type: str = 'standard',
        language: str = 'en-US'
    ) -> Optional[str]:
        """
        Get a human-readable label for a concept.
        
        Args:
            concept: Concept QName (e.g., 'us-gaap:Cash')
            label_type: Type of label ('standard', 'terse', 'verbose', 'documentation')
            language: Language code ('en-US', 'en', etc.)
            
        Returns:
            Label text or None if not found
        """
        concept_labels = self.labels.get(concept, {})
        type_labels = concept_labels.get(label_type, {})
        
        # Try exact language match
        if language in type_labels:
            return type_labels[language]
        
        # Try fallback to base language
        if '-' in language:
            base_lang = language.split('-')[0]
            if base_lang in type_labels:
                return type_labels[base_lang]
        
        # Try any available language for this type
        if type_labels:
            return next(iter(type_labels.values()))
        
        return None
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        name = self.metadata.get('name', 'unknown')
        version = self.metadata.get('version', 'unknown')
        role_count = len(self.roles)
        element_count = len(self.elements)
        calc_count = len(self.calculations)
        dim_count = len(self.dimensions.get('axes', {}))
        label_count = len(self.labels)
        
        return (
            f"TaxonomyProfile(name='{name}', version='{version}', "
            f"roles={role_count}, elements={element_count}, "
            f"calculations={calc_count}, dimensions={dim_count}, "
            f"labels={label_count})"
        )