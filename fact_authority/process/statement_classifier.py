# File: engines/fact_authority/process/statement_classifier.py
# Path: engines/fact_authority/process/statement_classifier.py

"""
Statement Classifier (Taxonomy-Driven)
=======================================

Classifies facts into statement types using TAXONOMY AUTHORITY.

CRITICAL DIFFERENCE from CCQ approach:
- OLD (CCQ): Analyze properties -> Predict statement (INDUCTIVE)
- NEW (Fact Authority): Lookup in taxonomy -> Assign statement (DEDUCTIVE)

The taxonomy is the authoritative source for statement placement.

Responsibilities:
    - Look up concept in taxonomy
    - Return taxonomy's statement assignment
    - Validate mapper placement against taxonomy
    
Does NOT:
    - Predict based on properties (CCQ does that)
    - Make guesses (taxonomy is truth)
    - Override taxonomy rules
"""

from typing import Dict, Any, Optional, Set
import re

from core.system_logger import get_logger

logger = get_logger(__name__)


class StatementClassifier:
    """
    Classifies concepts using taxonomy authority.
    
    Uses taxonomy's presentation linkbase to determine which
    statement each concept belongs to.
    
    This is DEDUCTIVE reasoning using taxonomy rules, not
    INDUCTIVE reasoning from properties.
    """
    
    # Standard statement types
    STATEMENT_TYPES = [
        'balance_sheet',
        'income_statement',
        'cash_flow',
        'other'
    ]
    
    # Role URI patterns for statement identification
    ROLE_PATTERNS = {
        'balance_sheet': [
            'StatementOfFinancialPosition',
            'BalanceSheet',
            'StatementOfFinancialPositionClassified',
            'ConsolidatedBalanceSheet'
        ],
        'income_statement': [
            'StatementOfIncome',
            'IncomeStatement',
            'StatementOfOperations',
            'StatementOfEarnings',
            'StatementOfComprehensiveIncome'
        ],
        'cash_flow': [
            'StatementOfCashFlows',
            'CashFlowStatement',
            'ConsolidatedStatementsOfCashFlows'
        ]
    }
    
    def __init__(self, taxonomy_data: Dict[str, Any]):
        """
        Initialize classifier with taxonomy data.
        
        Args:
            taxonomy_data: Taxonomy data from taxonomy_reader
        """
        self.logger = logger
        self.taxonomy_data = taxonomy_data
        
        # Extract concept-to-statement mappings from taxonomy
        self.concept_statements = self._extract_concept_statements()
        
        self.logger.info(
            f"StatementClassifier initialized with "
            f"{len(self.concept_statements)} concept mappings"
        )
    
    def classify_concept(self, concept_qname: str) -> Optional[str]:
        """
        Classify a concept using taxonomy authority.
        
        Args:
            concept_qname: Concept qualified name (e.g., 'us-gaap:Assets')
            
        Returns:
            Statement type ('balance_sheet', 'income_statement', 
                          'cash_flow', 'other') or None if not in taxonomy
        """
        # Normalize concept (remove year suffix)
        normalized = self._normalize_concept(concept_qname)
        
        # Look up in taxonomy
        statement = self.concept_statements.get(normalized)
        
        if statement:
            self.logger.debug(
                f"Concept '{concept_qname}' -> '{statement}' (from taxonomy)"
            )
        else:
            self.logger.debug(
                f"Concept '{concept_qname}' not found in taxonomy"
            )
        
        return statement
    
    def validate_placement(
        self,
        concept_qname: str,
        current_statement: str
    ) -> Dict[str, Any]:
        """
        Validate if concept placement matches taxonomy.
        
        Args:
            concept_qname: Concept qualified name
            current_statement: Statement where mapper placed it
            
        Returns:
            {
                'is_valid': bool,
                'expected_statement': str or None,
                'current_statement': str,
                'reason': str
            }
        """
        expected = self.classify_concept(concept_qname)
        
        # Concept not in taxonomy (likely extension)
        if expected is None:
            return {
                'is_valid': True,  # Accept extension concepts
                'expected_statement': None,
                'current_statement': current_statement,
                'reason': 'Concept not in taxonomy (likely extension)'
            }
        
        # Check if placement matches taxonomy
        is_valid = (expected == current_statement)
        
        return {
            'is_valid': is_valid,
            'expected_statement': expected,
            'current_statement': current_statement,
            'reason': (
                'Correct placement per taxonomy' if is_valid
                else f"Taxonomy assigns to '{expected}' but found in '{current_statement}'"
            )
        }
    
    def get_concepts_for_statement(self, statement_type: str) -> Set[str]:
        """
        Get all concepts that belong to a statement type per taxonomy.
        
        Args:
            statement_type: Statement type to query
            
        Returns:
            Set of concept qnames for that statement
        """
        concepts = set()
        
        for concept, stmt in self.concept_statements.items():
            if stmt == statement_type:
                concepts.add(concept)
        
        return concepts
    
    def _extract_concept_statements(self) -> Dict[str, str]:
        """
        Extract concept-to-statement mappings from taxonomy.
        
        This extracts the presentation linkbase information that
        shows which role (statement) each concept appears in.
        
        Returns:
            Dict mapping concept_qname to statement_type
        """
        concept_statements = {}
        
        # TODO: Extract from taxonomy_data
        # This depends on taxonomy_reader's output structure
        #
        # Expected structure from taxonomy_reader:
        # {
        #   'presentation_linkbase': {
        #     'roles': {
        #       'http://fasb.org/.../StatementOfFinancialPosition': {
        #         'statement_type': 'balance_sheet',
        #         'concepts': ['us-gaap:Assets', 'us-gaap:Liabilities', ...]
        #       },
        #       ...
        #     }
        #   }
        # }
        #
        # OR:
        # {
        #   'concepts': {
        #     'us-gaap:Assets': {
        #       'statement_type': 'balance_sheet',
        #       ...
        #     }
        #   }
        # }
        
        # For now, log warning that extraction not implemented
        self.logger.warning(
            "Taxonomy concept extraction not yet implemented - "
            "using empty mapping. "
            "Need to integrate with taxonomy_reader structure."
        )
        
        # When implemented, this should extract from:
        # - presentation_linkbase roles
        # - map role URI to statement type
        # - collect concepts for each statement
        
        return concept_statements
    
    def _classify_role_uri(self, role_uri: str) -> Optional[str]:
        """
        Classify role URI into statement type.
        
        Args:
            role_uri: XBRL role URI
            
        Returns:
            Statement type or None
        """
        # Check each statement type's patterns
        for statement_type, patterns in self.ROLE_PATTERNS.items():
            for pattern in patterns:
                if pattern in role_uri:
                    return statement_type
        
        # No match - probably a note or schedule
        return 'other'
    
    @staticmethod
    def _normalize_concept(concept: str) -> str:
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


__all__ = ['StatementClassifier']