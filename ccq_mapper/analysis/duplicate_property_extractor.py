# File: engines/ccq_mapper/analysis/duplicate_property_extractor.py

"""
Duplicate Property Extractor
=============================

Extracts properties from facts for duplicate classification.

Responsibility:
- Extract classification properties from facts
- Provide market-agnostic property extraction
- Support multi-dimensional classification

This is separate from fact_extractor (which extracts concept/context/value)
and focuses on properties needed for classification.
"""

from typing import Dict, Any


class DuplicatePropertyExtractor:
    """Extracts properties for duplicate classification."""
    
    @staticmethod
    def extract_properties(fact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract properties needed for classification.
        
        This is market-agnostic - works with any XBRL source.
        
        Args:
            fact: Fact dictionary
            
        Returns:
            Properties dictionary with:
            - period_type: Duration or instant
            - value_type: Type of value
            - unit: Unit reference
            - is_nil: Whether fact is nil
            - is_primary_context: Whether using primary context
            - decimals: Decimal precision
            - balance: Debit/credit balance
            - label: Human-readable label
            - concept_qname: Qualified concept name
        """
        return {
            'period_type': fact.get('period_type'),
            'value_type': fact.get('value_type'),
            'unit': fact.get('unit') or fact.get('unit_ref'),
            'is_nil': fact.get('is_nil', False),
            'is_primary_context': fact.get('is_primary_context', True),
            'decimals': fact.get('decimals'),
            'balance': fact.get('balance'),
            'label': fact.get('label', ''),
            'concept_qname': DuplicatePropertyExtractor._extract_concept(fact)
        }
    
    @staticmethod
    def _extract_concept(fact: Dict[str, Any]) -> str:
        """Extract concept from fact (market-agnostic)."""
        for field in ['concept_qname', 'concept', 'qname', 'name']:
            concept = fact.get(field)
            if concept:
                return str(concept)
        return None
    
    @staticmethod
    def extract_context(fact: Dict[str, Any]) -> str:
        """Extract context from fact (market-agnostic)."""
        for field in ['context_ref', 'contextRef', 'context_id', 'context']:
            context = fact.get(field)
            if context:
                return str(context)
        return None
    
    @staticmethod
    def extract_value(fact: Dict[str, Any]) -> Any:
        """Extract value from fact (market-agnostic)."""
        for field in ['fact_value', 'value', 'amount']:
            value = fact.get(field)
            if value is not None:
                return value
        return None


__all__ = ['DuplicatePropertyExtractor']