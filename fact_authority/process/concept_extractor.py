# File: engines/fact_authority/process/concept_extractor.py
# Path: engines/fact_authority/process/concept_extractor.py

"""
Concept Extractor
=================

Extracts concept-to-statement mappings from taxonomy data sources.

AUTHORITY ENGINE PRINCIPLE:
Uses ALL available data sources from TaxonomyProfile:
1. Calculation linkbases (if present) - most authoritative
2. Element properties (periodType + balance) - universal fallback
3. Future: Presentation linkbases, definition linkbases

Market agnostic - works with any taxonomy structure.
"""

from typing import Dict, Any, Set, Optional
import re

from core.system_logger import get_logger

logger = get_logger(__name__)


class ConceptExtractor:
    """
    Extracts concept classifications from taxonomy data.
    
    Consolidates multiple taxonomy data sources to build
    authoritative concept-to-statement mappings.
    """
    
    def __init__(self, role_classifier):
        """
        Initialize concept extractor.
        
        Args:
            role_classifier: RoleClassifier instance for role classification
        """
        self.logger = logger
        self.role_classifier = role_classifier
    
    def extract_taxonomy_concepts(self, taxonomy_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract concept-to-statement mappings from taxonomy.
        
        AUTHORITY ENGINE PRINCIPLE:
        Uses ALL available data sources from TaxonomyProfile:
        1. Calculation linkbases (if present) - most authoritative
        2. Element properties (periodType + balance) - universal fallback
        3. Future: Presentation linkbases, definition linkbases
        
        Market agnostic - works with any taxonomy structure and any
        combination of available data sources.
        
        Args:
            taxonomy_data: Taxonomy data (TaxonomyProfile object or dict)
        
        Returns:
            Dict mapping concept_qname to statement_type
        """
        concepts = {}
        
        if not taxonomy_data:
            self.logger.warning("No taxonomy data provided")
            return concepts
        
        # Handle both TaxonomyProfile object and dict
        taxonomy_dict = self._ensure_dict(taxonomy_data)
        
        # Get all available data sources
        roles = taxonomy_dict.get('roles', {})
        calculations = taxonomy_dict.get('calculations', {})
        elements = taxonomy_dict.get('elements', {})
        
        self.logger.info(
            f"Authority scan: {len(roles)} roles, {len(calculations)} calc linkbases, "
            f"{len(elements)} elements"
        )
        
        if not roles:
            self.logger.warning("No roles found - cannot classify concepts")
            return concepts
        
        # SOURCE 1: Extract from calculation linkbases (most authoritative)
        calc_concepts = self._extract_from_calculations_source(roles, calculations)
        self.logger.info(f"Source 1 (Calculations): {len(calc_concepts)} concepts")
        
        # SOURCE 2: Extract from element properties (universal fallback)
        element_concepts = self._extract_from_elements_source(elements)
        self.logger.info(f"Source 2 (Elements): {len(element_concepts)} concepts")
        
        # CONSOLIDATE: Merge all sources with priority
        # Strategy: Start with broad (elements), override with specific (calculations)
        concepts = element_concepts.copy()  # Universal XBRL properties
        concepts.update(calc_concepts)      # Specific taxonomy calculations
        
        self.logger.info(
            f"TOTAL: {len(concepts)} concepts from {len(calc_concepts) + len(element_concepts)} discoveries"
        )
        
        return concepts
    
    def _extract_from_calculations_source(
        self,
        roles: Dict[str, Any],
        calculations: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Extract concepts from calculation linkbases.
        
        Calculation linkbases show hierarchical relationships,
        making them authoritative for statement placement when present.
        
        Args:
            roles: Role definitions
            calculations: Calculation relationships by role
            
        Returns:
            Dict mapping concept to statement type
        """
        if not calculations:
            self.logger.debug("No calculation linkbases available")
            return {}
        
        concepts = {}
        role_count = 0
        
        for role_uri, role_info in roles.items():
            statement_type = self.role_classifier.classify_role(role_uri, role_info)
            
            if not statement_type:
                continue
            
            if role_uri in calculations:
                role_count += 1
                role_concepts = self._extract_concepts_from_calculations(
                    calculations[role_uri]
                )
                
                for concept in role_concepts:
                    normalized = self.normalize_concept(concept)
                    if normalized not in concepts:
                        concepts[normalized] = statement_type
        
        if role_count > 0:
            self.logger.info(f"  Processed {role_count} roles with calculations")
        
        return concepts
    
    def _extract_from_elements_source(
        self,
        elements: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Extract concepts from element properties.
        
        Uses XBRL element properties (periodType, balance) to classify.
        This is UNIVERSAL - works for ANY taxonomy as these are XBRL spec requirements.
        
        Classification (XBRL spec - market agnostic):
        - periodType="instant" → balance_sheet (point in time)
        - periodType="duration" → income/cash flow (period)
        - Cash patterns → cash_flow
        - Default duration → income_statement
        
        Args:
            elements: Element properties by concept qname
            
        Returns:
            Dict mapping concept to statement type
        """
        if not elements:
            self.logger.warning("No elements available")
            return {}
        
        concepts = {}
        stats = {'balance_sheet': 0, 'income_statement': 0, 'cash_flow': 0, 'skipped': 0}
        
        for concept_qname, properties in elements.items():
            period_type = (properties.get('period_type') or '').lower()
            abstract = properties.get('abstract', False)
            
            # Skip abstract concepts (structural, not data)
            if abstract:
                stats['skipped'] += 1
                continue
            
            normalized = self.normalize_concept(concept_qname)
            statement_type = None
            
            if period_type == 'instant':
                # Instant = Balance Sheet
                statement_type = 'balance_sheet'
                stats['balance_sheet'] += 1
                
            elif period_type == 'duration':
                # Duration = Flow statement
                concept_lower = concept_qname.lower()
                
                # Universal cash flow patterns
                cash_patterns = [
                    'cash', 'payment', 'receipt', 'proceeds', 
                    'expenditure', 'disbursement', 'financing',
                    'investing', 'operating'
                ]
                
                if any(p in concept_lower for p in cash_patterns):
                    statement_type = 'cash_flow'
                    stats['cash_flow'] += 1
                else:
                    statement_type = 'income_statement'
                    stats['income_statement'] += 1
            
            if statement_type:
                concepts[normalized] = statement_type
        
        self.logger.info(
            f"  Element classification: BS={stats['balance_sheet']}, "
            f"IS={stats['income_statement']}, CF={stats['cash_flow']}, "
            f"Skipped={stats['skipped']}"
        )
        
        return concepts
    
    def _extract_concepts_from_calculations(
        self,
        role_calculations: Dict[str, Any]
    ) -> Set[str]:
        """
        Extract all concepts from calculation relationships in a role.
        
        Args:
            role_calculations: Calculation data for one role
                              {concept: {children: [{concept, weight}]}}
            
        Returns:
            Set of concept qnames
        """
        concepts = set()
        
        # role_calculations is a dict of concept -> children
        for parent_concept, calc_info in role_calculations.items():
            # Add parent concept
            concepts.add(parent_concept)
            
            # Add child concepts
            children = calc_info.get('children', [])
            for child in children:
                if isinstance(child, dict):
                    child_concept = child.get('concept')
                    if child_concept:
                        concepts.add(child_concept)
                elif isinstance(child, str):
                    concepts.add(child)
        
        return concepts
    
    @staticmethod
    def normalize_concept(concept: str) -> str:
        """
        Normalize concept qname for comparison.
        
        Removes year suffix from namespace.
        
        Examples:
            us-gaap-2024:Assets -> us-gaap:Assets
            dei-2023:EntityName -> dei:EntityName
            
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
    
    def _ensure_dict(self, taxonomy_data: Any) -> Dict[str, Any]:
        """
        Convert taxonomy data to dict format if needed.
        
        Args:
            taxonomy_data: TaxonomyProfile object or dict or None
            
        Returns:
            Dictionary representation
        """
        if hasattr(taxonomy_data, 'to_dict'):
            self.logger.debug("Converted TaxonomyProfile to dict")
            return taxonomy_data.to_dict()
        elif isinstance(taxonomy_data, dict):
            self.logger.debug("Taxonomy data is already a dict")
            return taxonomy_data
        else:
            self.logger.warning(f"Unexpected taxonomy_data type: {type(taxonomy_data)}")
            return {}


__all__ = ['ConceptExtractor']