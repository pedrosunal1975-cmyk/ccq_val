# File: core/taxonomy_builder.py
# Path: core/taxonomy_builder.py

"""
Taxonomy Builder
================

Builds taxonomy accessors from normalization metadata.

Responsibilities:
- Extract taxonomy information from normalized data
- Parse taxonomy names and versions
- Initialize MultiTaxonomyAccessor
- Handle failures gracefully
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from core.system_logger import get_logger

logger = get_logger(__name__)


class TaxonomyBuilder:
    """
    Builds MultiTaxonomyAccessor from normalization metadata.
    
    Extracts taxonomy information and initializes accessor for
    validation engines.
    """
    
    def __init__(self, taxonomy_path: Optional[str] = None):
        """
        Initialize taxonomy builder.
        
        Args:
            taxonomy_path: Path to taxonomy libraries
        """
        self.taxonomy_path = Path(taxonomy_path) if taxonomy_path else None
        self.logger = logger
    
    def build_taxonomy_accessor(
        self,
        normalized_data: Dict[str, Any]
    ) -> Optional[Any]:  # Returns MultiTaxonomyAccessor or None
        """
        Build MultiTaxonomyAccessor from normalization metadata.
        
        Args:
            normalized_data: Normalized data containing metadata with taxonomies_used
            
        Returns:
            MultiTaxonomyAccessor instance or None if failed
        """
        if not self.taxonomy_path:
            self.logger.warning(
                "No taxonomy_path configured - validation will use fallback methods"
            )
            return None
        
        try:
            # Import here to avoid circular dependencies
            from core.taxonomy import MultiTaxonomyAccessor
            
            # Get discovered taxonomies from normalization metadata
            taxonomies_used = normalized_data['metadata'].get('taxonomies_used', [])
            
            if not taxonomies_used:
                self.logger.warning(
                    "No taxonomies discovered - validation will use fallback methods"
                )
                return None
            
            self.logger.info(
                f"Building MultiTaxonomyAccessor with {len(taxonomies_used)} taxonomies"
            )
            
            # Initialize MultiTaxonomyAccessor
            taxonomy_accessor = MultiTaxonomyAccessor(
                taxonomy_path=self.taxonomy_path
            )
            
            # Parse taxonomy names and versions
            taxonomy_list = self._parse_taxonomy_list(taxonomies_used)
            
            # Load all taxonomies
            taxonomy_accessor.load_taxonomies(taxonomy_list)
            
            loaded = taxonomy_accessor.get_loaded_taxonomies()
            self.logger.info(
                f"✓ MultiTaxonomyAccessor ready with: {loaded}"
            )
            
            return taxonomy_accessor
            
        except ImportError as e:
            self.logger.error(
                f"Cannot import MultiTaxonomyAccessor: {e}. "
                "Validation will use fallback methods."
            )
            return None
        except Exception as e:
            self.logger.error(
                f"Failed to build MultiTaxonomyAccessor: {e}",
                exc_info=True
            )
            return None
    
    def _parse_taxonomy_list(
        self,
        taxonomies_used: List[str]
    ) -> List[Dict[str, str]]:
        """
        Parse taxonomy names into structured format.
        
        Args:
            taxonomies_used: List of taxonomy strings (e.g., ['us-gaap/2024', 'dei'])
            
        Returns:
            List of dicts with 'name' and 'year' keys
            
        Examples:
            ['us-gaap/2024', 'dei'] -> [
                {'name': 'us-gaap', 'year': '2024'},
                {'name': 'dei', 'year': 'latest'}
            ]
        """
        taxonomy_list = []
        
        for tax_name in taxonomies_used:
            # Parse "us-gaap/2024" format
            if '/' in tax_name:
                name, year = tax_name.split('/', 1)
                taxonomy_list.append({'name': name, 'year': year})
            else:
                # No version specified, use latest
                taxonomy_list.append({'name': tax_name, 'year': 'latest'})
        
        return taxonomy_list


__all__ = ['TaxonomyBuilder']