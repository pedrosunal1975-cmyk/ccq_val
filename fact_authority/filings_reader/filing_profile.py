# File: filing_profile.py
# Location: engines/fact_authority/filings_reader/filing_profile.py

"""
Filing Profile
==============

Data structure for company XBRL filing metadata and file locations.

Stores discovered file paths, market information, extension namespace,
and validation status for a company XBRL filing.

This profile enables fact_authority to understand company-specific extensions
and taxonomy structure across SEC, FCA, and ESMA markets.

Classes:
    FilingProfile: Complete metadata for a company filing
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


@dataclass
class FilingProfile:
    """
    Complete metadata profile for a company XBRL filing.
    
    Stores all discovered files, their locations, market information,
    extension namespace, and validation status. This enables fact_authority
    to understand company-specific extensions and taxonomy structure.
    
    Attributes:
        metadata: Basic filing information (company, market, date)
        structure: Directory structure information
        files: Discovered XBRL file locations
        extension_namespace: Company extension namespace (e.g., 'aapl')
        taxonomy_year: Year of taxonomy (e.g., '2024')
        validation: File accessibility and completeness status
        format_version: Profile format version
        discovered_at: Timestamp of discovery
    """
    
    # Basic metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    
    # Directory structure
    structure: Dict[str, Any] = field(default_factory=dict)
    
    # Discovered files organized by type
    files: Dict[str, Any] = field(default_factory=dict)
    
    # Extension information
    extension_namespace: Optional[str] = None
    taxonomy_year: Optional[str] = None
    
    # Validation status
    validation: Dict[str, Any] = field(default_factory=dict)
    
    # Version control
    format_version: str = '1.0'
    discovered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def get_extension_schema(self) -> Optional[Path]:
        """
        Get path to company extension schema file.
        
        Returns:
            Path to extension .xsd file or None
        """
        return self.files.get('extension_schema')
    
    def get_presentation_linkbases(self) -> List[Path]:
        """
        Get all presentation linkbase files.
        
        Returns:
            List of presentation linkbase paths
        """
        return self.files.get('presentation', [])
    
    def get_calculation_linkbases(self) -> List[Path]:
        """
        Get all calculation linkbase files.
        
        Returns:
            List of calculation linkbase paths
        """
        return self.files.get('calculation', [])
    
    def get_definition_linkbases(self) -> List[Path]:
        """
        Get all definition linkbase files.
        
        Returns:
            List of definition linkbase paths
        """
        return self.files.get('definition', [])
    
    def get_label_linkbases(self) -> List[Path]:
        """
        Get all label linkbase files.
        
        Returns:
            List of label linkbase paths
        """
        return self.files.get('label', [])
    
    def get_instance_file(self) -> Optional[Path]:
        """
        Get instance document file (XML or iXBRL).
        
        Returns:
            Path to instance file or None
        """
        instances = self.files.get('instance', [])
        return instances[0] if instances else None
    
    def is_complete(self) -> bool:
        """
        Check if filing has all required components.
        
        Returns:
            True if filing is complete and accessible
        """
        return self.validation.get('all_files_accessible', False)
    
    def has_extensions(self) -> bool:
        """
        Check if filing has company extensions.
        
        Returns:
            True if company extension schema exists
        """
        return self.get_extension_schema() is not None
    
    def get_market(self) -> str:
        """
        Get regulatory market (SEC, FCA, ESMA).
        
        Returns:
            Market identifier
        """
        return self.metadata.get('market', 'unknown')
    
    def get_company(self) -> str:
        """
        Get company identifier.
        
        Returns:
            Company identifier
        """
        return self.metadata.get('company', 'unknown')
    
    def to_dict(self) -> dict:
        """
        Convert profile to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'metadata': self.metadata,
            'structure': self._structure_to_dict(),
            'files': self._files_to_dict(),
            'extension_namespace': self.extension_namespace,
            'taxonomy_year': self.taxonomy_year,
            'validation': self.validation,
            'format_version': self.format_version,
            'discovered_at': self.discovered_at
        }
    
    def _structure_to_dict(self) -> dict:
        """Convert structure paths to strings."""
        structure_dict = {}
        for key, value in self.structure.items():
            if isinstance(value, Path):
                structure_dict[key] = str(value)
            else:
                structure_dict[key] = value
        return structure_dict
    
    def _files_to_dict(self) -> dict:
        """Convert file paths to strings."""
        files_dict = {}
        for key, value in self.files.items():
            if isinstance(value, Path):
                files_dict[key] = str(value)
            elif isinstance(value, list):
                files_dict[key] = [str(p) if isinstance(p, Path) else p for p in value]
            else:
                files_dict[key] = value
        return files_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FilingProfile':
        """
        Create profile from dictionary.
        
        Args:
            data: Dictionary with profile data
            
        Returns:
            FilingProfile instance
        """
        profile = cls()
        profile.metadata = data.get('metadata', {})
        profile.structure = cls._structure_from_dict(data.get('structure', {}))
        profile.files = cls._files_from_dict(data.get('files', {}))
        profile.extension_namespace = data.get('extension_namespace')
        profile.taxonomy_year = data.get('taxonomy_year')
        profile.validation = data.get('validation', {})
        profile.format_version = data.get('format_version', '1.0')
        profile.discovered_at = data.get('discovered_at', '')
        
        return profile
    
    @classmethod
    def _structure_from_dict(cls, data: dict) -> dict:
        """Convert string paths to Path objects."""
        structure = {}
        for key, value in data.items():
            if key.endswith('_path') or key == 'base_path':
                structure[key] = Path(value) if value else None
            else:
                structure[key] = value
        return structure
    
    @classmethod
    def _files_from_dict(cls, data: dict) -> dict:
        """Convert string paths to Path objects."""
        files = {}
        for key, value in data.items():
            if isinstance(value, str):
                files[key] = Path(value) if value else None
            elif isinstance(value, list):
                files[key] = [Path(p) if isinstance(p, str) else p for p in value]
            else:
                files[key] = value
        return files
    
    def to_json(self) -> str:
        """
        Serialize to JSON string.
        
        Returns:
            JSON representation
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_string: str) -> 'FilingProfile':
        """
        Deserialize from JSON string.
        
        Args:
            json_string: JSON representation
            
        Returns:
            FilingProfile instance
        """
        data = json.loads(json_string)
        return cls.from_dict(data)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        company = self.get_company()
        market = self.get_market()
        has_ext = "with extensions" if self.has_extensions() else "no extensions"
        complete = "complete" if self.is_complete() else "incomplete"
        
        return (
            f"FilingProfile(company='{company}', market='{market}', "
            f"{has_ext}, {complete})"
        )