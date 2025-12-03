# File: engines/fact_authority/process/xbrl_filings.py
# Path: engines/fact_authority/process/xbrl_filings.py

"""
XBRL Filings Consolidator
==========================

Consolidates company XBRL extensions with base taxonomy.

Purpose:
    Bridge between company-specific extensions (from filings_reader)
    and standard taxonomy (from taxonomy_reader) to provide unified
    concept definitions.

Responsibilities:
    - Merge extension concepts with base taxonomy
    - Resolve concept definitions (extension vs base)
    - Provide unified concept lookup
    - Validate extension against taxonomy rules

Does NOT:
    - Parse XBRL files (filings_reader does that)
    - Parse taxonomy files (taxonomy_reader does that)
    - Make validation decisions (reconciler does that)
"""

from typing import Dict, Any, Optional, Set
import re

from core.system_logger import get_logger

logger = get_logger(__name__)


class XBRLFilingsConsolidator:
    """
    Consolidates XBRL filing extensions with base taxonomy.
    
    Provides unified interface to concept definitions regardless
    of whether they come from extensions or base taxonomy.
    """
    
    def __init__(
        self,
        taxonomy_data: Dict[str, Any],
        filing_data: Dict[str, Any]
    ):
        """
        Initialize consolidator with taxonomy and filing data.
        
        Args:
            taxonomy_data: Base taxonomy from taxonomy_reader
            filing_data: XBRL filing data from filings_reader
        """
        self.logger = logger
        self.taxonomy_data = taxonomy_data
        self.filing_data = filing_data
        
        # Build unified concept map
        self.unified_concepts = self._build_unified_concepts()
        
        self.logger.info(
            f"XBRLFilingsConsolidator initialized with "
            f"{len(self.unified_concepts)} unified concepts"
        )
    
    def get_concept_definition(self, concept_qname: str) -> Optional[Dict[str, Any]]:
        """
        Get unified concept definition.
        
        Looks up concept in extensions first, then base taxonomy.
        
        Args:
            concept_qname: Concept qualified name
            
        Returns:
            Concept definition dict or None
        """
        normalized = self._normalize_concept(concept_qname)
        
        concept_def = self.unified_concepts.get(normalized)
        
        if concept_def:
            self.logger.debug(
                f"Found concept '{concept_qname}' "
                f"(source: {concept_def.get('source')})"
            )
        else:
            self.logger.debug(f"Concept '{concept_qname}' not found")
        
        return concept_def
    
    def get_concept_statement(self, concept_qname: str) -> Optional[str]:
        """
        Get statement assignment for concept.
        
        Args:
            concept_qname: Concept qualified name
            
        Returns:
            Statement type or None
        """
        concept_def = self.get_concept_definition(concept_qname)
        
        if not concept_def:
            return None
        
        return concept_def.get('statement_type')
    
    def is_extension_concept(self, concept_qname: str) -> bool:
        """
        Check if concept is a company extension.
        
        Args:
            concept_qname: Concept qualified name
            
        Returns:
            True if extension, False if base taxonomy
        """
        concept_def = self.get_concept_definition(concept_qname)
        
        if not concept_def:
            return False
        
        return concept_def.get('source') == 'extension'
    
    def get_extension_base_concept(self, extension_qname: str) -> Optional[str]:
        """
        Get base concept for extension concept.
        
        Uses substitutionGroup to find parent concept.
        
        Args:
            extension_qname: Extension concept qualified name
            
        Returns:
            Base concept qname or None
        """
        concept_def = self.get_concept_definition(extension_qname)
        
        if not concept_def or concept_def.get('source') != 'extension':
            return None
        
        return concept_def.get('base_concept')
    
    def validate_concept(self, concept_qname: str) -> Dict[str, Any]:
        """
        Validate concept definition.
        
        Args:
            concept_qname: Concept qualified name
            
        Returns:
            Validation result dict
        """
        concept_def = self.get_concept_definition(concept_qname)
        
        if not concept_def:
            return {
                'is_valid': False,
                'reason': 'Concept not found in taxonomy or extensions'
            }
        
        # Extension concepts should have valid base
        if concept_def.get('source') == 'extension':
            base_concept = concept_def.get('base_concept')
            
            if not base_concept:
                return {
                    'is_valid': False,
                    'reason': 'Extension concept missing base concept (substitutionGroup)'
                }
            
            base_def = self.get_concept_definition(base_concept)
            if not base_def:
                return {
                    'is_valid': False,
                    'reason': f"Base concept '{base_concept}' not found in taxonomy"
                }
        
        return {
            'is_valid': True,
            'reason': 'Concept definition valid'
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get consolidation statistics.
        
        Returns:
            Statistics dict
        """
        total = len(self.unified_concepts)
        extension_count = sum(
            1 for c in self.unified_concepts.values()
            if c.get('source') == 'extension'
        )
        base_count = total - extension_count
        
        return {
            'total_concepts': total,
            'base_taxonomy_concepts': base_count,
            'extension_concepts': extension_count,
            'extension_percentage': round((extension_count / total * 100), 1) if total > 0 else 0
        }
    
    def _build_unified_concepts(self) -> Dict[str, Dict[str, Any]]:
        """
        Build unified concept map from taxonomy and extensions.
        
        Returns:
            Dict mapping concept_qname to unified definition
        """
        unified = {}
        
        # Add base taxonomy concepts
        base_concepts = self._extract_base_concepts()
        for concept_qname, concept_def in base_concepts.items():
            unified[concept_qname] = {
                **concept_def,
                'source': 'base_taxonomy'
            }
        
        # Add extension concepts (overwrite if duplicate)
        extension_concepts = self._extract_extension_concepts()
        for concept_qname, concept_def in extension_concepts.items():
            unified[concept_qname] = {
                **concept_def,
                'source': 'extension'
            }
        
        self.logger.info(
            f"Built unified concepts: "
            f"{len(base_concepts)} base + "
            f"{len(extension_concepts)} extensions = "
            f"{len(unified)} total"
        )
        
        return unified
    
    def _extract_base_concepts(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract concepts from base taxonomy.
        
        Returns:
            Dict mapping concept_qname to definition
        """
        base_concepts = {}
        
        # TODO: Extract from taxonomy_data
        # This depends on taxonomy_reader's output structure
        #
        # Expected structure:
        # {
        #   'concepts': {
        #     'us-gaap:Assets': {
        #       'type': 'monetary',
        #       'periodType': 'instant',
        #       'balance': 'debit',
        #       'statement_type': 'balance_sheet',
        #       ...
        #     }
        #   }
        # }
        
        self.logger.warning(
            "Base concept extraction not yet implemented - "
            "using empty dict. "
            "Need to integrate with taxonomy_reader structure."
        )
        
        return base_concepts
    
    def _extract_extension_concepts(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract concepts from company extensions.
        
        Returns:
            Dict mapping concept_qname to definition
        """
        extension_concepts = {}
        
        # Extract from filing_data
        extension_schema = self.filing_data.get('extension_schema', {})
        
        if not extension_schema:
            self.logger.debug("No extension schema in filing data")
            return extension_concepts
        
        concepts = extension_schema.get('concepts', {})
        
        for concept_qname, concept_data in concepts.items():
            # Only include actual extensions
            if not self._is_extension_namespace(concept_qname):
                continue
            
            extension_concepts[concept_qname] = {
                'type': concept_data.get('type'),
                'periodType': concept_data.get('periodType'),
                'balance': concept_data.get('balance'),
                'base_concept': concept_data.get('substitutionGroup'),
                'abstract': concept_data.get('abstract', False),
                'nillable': concept_data.get('nillable', True)
            }
        
        return extension_concepts
    
    def _is_extension_namespace(self, concept_qname: str) -> bool:
        """
        Check if concept qname is from extension namespace.
        
        Args:
            concept_qname: Concept qualified name
            
        Returns:
            True if extension namespace
        """
        if not concept_qname or ':' not in concept_qname:
            return False
        
        namespace = concept_qname.split(':')[0]
        
        # Standard taxonomy namespaces
        standard_namespaces = [
            'us-gaap',
            'ifrs-full',
            'ifrs',
            'dei',
            'srt',
            'country',
            'currency',
            'exch',
            'stpr',
            'naics',
            'sic',
            'uk-gaap',
            'esef'
        ]
        
        # Remove year suffix for comparison
        base_namespace = namespace.split('-')[0] if '-' in namespace else namespace
        
        return base_namespace not in [ns.split('-')[0] for ns in standard_namespaces]
    
    @staticmethod
    def _normalize_concept(concept: str) -> str:
        """
        Normalize concept qname for comparison.
        
        Removes year suffix from namespace.
        
        Args:
            concept: Concept qname
            
        Returns:
            Normalized concept qname
        """
        if not concept or ':' not in concept:
            return concept
        
        # Remove year suffix: -YYYY:
        normalized = re.sub(r'-\d{4}:', ':', concept)
        
        return normalized


__all__ = ['XBRLFilingsConsolidator']