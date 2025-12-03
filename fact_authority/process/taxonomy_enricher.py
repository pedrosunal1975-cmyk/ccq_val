# File: engines/fact_authority/process/taxonomy_enricher.py
# Path: engines/fact_authority/process/taxonomy_enricher.py

"""
Taxonomy Enricher
=================

Enriches base taxonomy with company extension concepts.

Responsibilities:
    - Add extension concepts to taxonomy
    - Map extensions to their base concepts
    - Preserve extension properties for classification
"""

from typing import Dict, Any
from core.system_logger import get_logger

logger = get_logger(__name__)


class TaxonomyEnricher:
    """
    Enriches taxonomy data with extension concept mappings.
    
    Adds extension concepts to taxonomy by mapping them to their base
    concepts through substitutionGroup inheritance. This allows the
    reconciler to validate extension concepts as if they were base concepts.
    
    Market agnostic - works with any taxonomy and extension structure.
    """
    
    def enrich_taxonomy_with_extensions(
        self,
        taxonomy_data: Dict[str, Any],
        extension_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich taxonomy data with extension concept mappings.
        
        Args:
            taxonomy_data: Base taxonomy data (TaxonomyProfile object or dict)
            extension_data: Extension tracing results from ExtensionInheritanceTracer
            
        Returns:
            Enriched taxonomy data dict with extension concepts included
        """
        if not extension_data:
            logger.debug("No extension data to enrich taxonomy")
            return self._ensure_dict(taxonomy_data)
        
        # Convert TaxonomyProfile to dict if needed
        enriched = self._ensure_dict(taxonomy_data)
        
        # Get extension concepts from tracing results
        extension_concepts = extension_data.get('extension_concepts', {})
        
        if not extension_concepts:
            logger.debug("No extension concepts to add")
            return enriched
        
        # Ensure elements dict exists
        if 'elements' not in enriched:
            enriched['elements'] = {}
        
        # Add non-abstract extension concepts to elements dict
        added_count = 0
        
        for ext_concept, ext_props in extension_concepts.items():
            is_abstract = ext_props.get('abstract', False)
            
            # Skip abstract concepts (structural only)
            if is_abstract:
                continue
            
            # Add extension to elements dict with its properties
            # StatementReconciler will classify it using the same logic as base concepts
            enriched['elements'][ext_concept] = {
                'period_type': (ext_props.get('periodType') or '').lower(),
                'balance': (ext_props.get('balance') or '').lower(),
                'abstract': False,
                'type': ext_props.get('type'),
                'nillable': ext_props.get('nillable', True)
            }
            added_count += 1
        
        logger.info(
            f"Enriched taxonomy with {added_count} extension concepts "
            f"added to elements dict for classification"
        )
        
        return enriched
    
    def _ensure_dict(self, taxonomy_data: Any) -> Dict[str, Any]:
        """
        Convert taxonomy data to dict format if needed.
        
        Args:
            taxonomy_data: TaxonomyProfile object or dict or None
            
        Returns:
            Dictionary representation
        """
        if not taxonomy_data:
            return {}
        
        if hasattr(taxonomy_data, 'to_dict'):
            return taxonomy_data.to_dict()
        
        if isinstance(taxonomy_data, dict):
            return taxonomy_data.copy()
        
        logger.warning(f"Unexpected taxonomy_data type: {type(taxonomy_data)}")
        return {}


__all__ = ['TaxonomyEnricher']