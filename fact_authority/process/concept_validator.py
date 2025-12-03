# File: engines/fact_authority/process/concept_validator.py
# Path: engines/fact_authority/process/concept_validator.py

"""
Concept Validator
=================

Validates concept placements against taxonomy authority.

Handles extension concept resolution through substitutionGroup inheritance.
Market agnostic - works with any extension structure.
"""

from typing import Dict, Any, Optional
from core.system_logger import get_logger

logger = get_logger(__name__)


class ConceptValidator:
    """
    Validates concept placements against taxonomy.
    
    Resolves extensions through inheritance and validates
    placements match taxonomy authority.
    """
    
    def __init__(
        self,
        taxonomy_concepts: Dict[str, str],
        extension_mappings: Dict[str, str],
        concept_normalizer
    ):
        """
        Initialize concept validator.
        
        Args:
            taxonomy_concepts: Dict mapping concept to statement type
            extension_mappings: Dict mapping extension to base concept
            concept_normalizer: Function to normalize concept names
        """
        self.logger = logger
        self.taxonomy_concepts = taxonomy_concepts
        self.extension_mappings = extension_mappings
        self.normalize_concept = concept_normalizer
    
    def validate_placement(
        self,
        concept: str,
        normalized_concept: str,
        current_statement: str,
        in_map_pro: bool,
        in_ccq: bool
    ) -> Dict[str, Any]:
        """
        Validate if concept placement matches taxonomy.
        
        If concept is an extension, attempts to resolve it through
        substitutionGroup inheritance to find base concept's statement assignment.
        Market agnostic - works with any extension structure.
        
        Args:
            concept: Original concept qname
            normalized_concept: Normalized concept qname
            current_statement: Statement being validated
            in_map_pro: Whether concept is in Map Pro
            in_ccq: Whether concept is in CCQ
            
        Returns:
            {
                'is_valid': bool,
                'category': str,
                'reason': str
            }
        """
        # Look up taxonomy statement (with extension resolution)
        taxonomy_statement = self._resolve_taxonomy_statement(
            concept,
            normalized_concept
        )
        
        # Concept not in taxonomy and no valid inheritance
        if taxonomy_statement is None:
            return {
                'is_valid': True,  # Accept it anyway (extension without inheritance)
                'category': 'not_in_taxonomy',
                'reason': 'Concept not found in taxonomy (extension without valid inheritance)'
            }
        
        # Check if placement matches taxonomy
        matches_taxonomy = (taxonomy_statement == current_statement)
        
        if matches_taxonomy:
            # Correct placement
            if in_map_pro and in_ccq:
                category = 'taxonomy_correct_both'
            elif in_map_pro:
                category = 'taxonomy_correct_map_pro_only'
            else:
                category = 'taxonomy_correct_ccq_only'
            
            return {
                'is_valid': True,
                'category': category,
                'reason': 'Correct placement per taxonomy'
            }
        else:
            # Incorrect placement
            return {
                'is_valid': False,
                'category': 'taxonomy_correct_neither',
                'reason': (
                    f"Taxonomy assigns to '{taxonomy_statement}' "
                    f"but found in '{current_statement}'"
                )
            }
    
    def _resolve_taxonomy_statement(
        self,
        concept: str,
        normalized_concept: str
    ) -> Optional[str]:
        """
        Resolve taxonomy statement for concept, including extension resolution.
        
        Args:
            concept: Original concept qname
            normalized_concept: Normalized concept qname
            
        Returns:
            Statement type or None
        """
        # Direct lookup in taxonomy
        taxonomy_statement = self.taxonomy_concepts.get(normalized_concept)
        
        # If not found and extension mappings exist, try resolution
        if taxonomy_statement is None and self.extension_mappings:
            taxonomy_statement = self._resolve_extension(concept, normalized_concept)
        
        return taxonomy_statement
    
    def _resolve_extension(
        self,
        concept: str,
        normalized_concept: str
    ) -> Optional[str]:
        """
        Resolve extension concept through substitutionGroup inheritance.
        
        Args:
            concept: Original concept qname
            normalized_concept: Normalized concept qname
            
        Returns:
            Statement type or None
        """
        # Try to resolve through extension mapping
        base_concept = self.extension_mappings.get(concept)
        if not base_concept:
            # Try normalized version
            base_concept = self.extension_mappings.get(normalized_concept)
        
        if base_concept:
            # Normalize base concept and look up in taxonomy
            normalized_base = self.normalize_concept(base_concept)
            taxonomy_statement = self.taxonomy_concepts.get(normalized_base)
            
            if taxonomy_statement:
                self.logger.debug(
                    f"Extension {concept} resolved to base {base_concept} "
                    f"-> {taxonomy_statement}"
                )
                return taxonomy_statement
        
        return None


__all__ = ['ConceptValidator']