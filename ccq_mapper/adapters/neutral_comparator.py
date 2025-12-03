"""
Neutral Comparator
==================

Compares financial statements that have been translated to neutral format.

Location: engines/ccq_mapper/adapters/neutral_comparator.py

This comparator only works with neutral format - it never touches
the original Map Pro or CCQ formats directly.
"""

from typing import Dict, Any, List, Set
from collections import defaultdict
from datetime import datetime

from .neutral_format import NeutralFact


class NeutralComparator:
    """
    Compares facts in neutral format.
    
    Responsibilities:
    - Group facts by concept_id
    - Compare values for shared concepts
    - Identify concepts unique to each system
    - Report differences neutrally (no judgments)
    
    Does NOT:
    - Judge which system is "correct"
    - Calculate success/agreement percentages
    - Prefer one system over another
    """
    
    VERSION = "1.0.0"
    
    def __init__(self):
        """Initialize neutral comparator."""
        self.version = self.VERSION
    
    def compare(
        self,
        map_pro_facts: List[NeutralFact],
        ccq_facts: List[NeutralFact],
        statement_type: str = 'unknown'
    ) -> Dict[str, Any]:
        """
        Compare two sets of neutral facts.
        
        Args:
            map_pro_facts: Facts from Map Pro (in neutral format)
            ccq_facts: Facts from CCQ (in neutral format)
            statement_type: Type of statement being compared
            
        Returns:
            Comparison results dictionary
        """
        # Build indexes by concept_id
        map_pro_by_concept = self._index_by_concept(map_pro_facts)
        ccq_by_concept = self._index_by_concept(ccq_facts)
        
        # Find all concepts
        all_concepts = set(map_pro_by_concept.keys()) | set(ccq_by_concept.keys())
        
        # Categorize concepts
        in_both = set(map_pro_by_concept.keys()) & set(ccq_by_concept.keys())
        map_pro_only = set(map_pro_by_concept.keys()) - set(ccq_by_concept.keys())
        ccq_only = set(ccq_by_concept.keys()) - set(map_pro_by_concept.keys())
        
        # Compare concepts that appear in both
        comparisons = []
        for concept_id in sorted(in_both):
            comparison = self._compare_concept(
                concept_id,
                map_pro_by_concept[concept_id],
                ccq_by_concept[concept_id]
            )
            comparisons.append(comparison)
        
        # Build results
        results = {
            'comparison': {
                'statement_type': statement_type,
                'compared_at': datetime.utcnow().isoformat(),
                'comparator_version': self.version
            },
            'summary': {
                'total_concepts': len(all_concepts),
                'in_both_systems': len(in_both),
                'map_pro_only': len(map_pro_only),
                'ccq_only': len(ccq_only),
                'map_pro_total_facts': len(map_pro_facts),
                'ccq_total_facts': len(ccq_facts),
                'map_pro_unique_concepts': len(map_pro_by_concept),
                'ccq_unique_concepts': len(ccq_by_concept)
            },
            'concepts_in_both': comparisons,
            'concepts_map_pro_only': self._summarize_concepts(
                map_pro_only,
                map_pro_by_concept
            ),
            'concepts_ccq_only': self._summarize_concepts(
                ccq_only,
                ccq_by_concept
            )
        }
        
        return results
    
    def _index_by_concept(
        self,
        facts: List[NeutralFact]
    ) -> Dict[str, List[NeutralFact]]:
        """
        Index facts by concept_id.
        
        Args:
            facts: List of neutral facts
            
        Returns:
            Dictionary mapping concept_id to list of facts
        """
        index = defaultdict(list)
        for fact in facts:
            index[fact.concept_id].append(fact)
        return dict(index)
    
    def _compare_concept(
        self,
        concept_id: str,
        map_pro_facts: List[NeutralFact],
        ccq_facts: List[NeutralFact]
    ) -> Dict[str, Any]:
        """
        Compare a single concept that appears in both systems.
        
        Args:
            concept_id: Concept identifier
            map_pro_facts: Map Pro facts for this concept
            ccq_facts: CCQ facts for this concept
            
        Returns:
            Comparison dictionary for this concept
        """
        # Compare fact counts
        map_pro_count = len(map_pro_facts)
        ccq_count = len(ccq_facts)
        
        # Get sample facts
        map_pro_sample = map_pro_facts[0] if map_pro_facts else None
        ccq_sample = ccq_facts[0] if ccq_facts else None
        
        # Compare values (simple - could be more sophisticated)
        value_match = self._compare_values(map_pro_facts, ccq_facts)
        
        return {
            'concept_id': concept_id,
            'concept_namespace': map_pro_sample.concept_namespace if map_pro_sample else '',
            'concept_local_name': map_pro_sample.concept_local_name if map_pro_sample else '',
            'label': map_pro_sample.label if map_pro_sample else '',
            'fact_counts': {
                'map_pro': map_pro_count,
                'ccq': ccq_count,
                'count_match': map_pro_count == ccq_count
            },
            'values': value_match,
            'map_pro_facts': [self._summarize_fact(f) for f in map_pro_facts],
            'ccq_facts': [self._summarize_fact(f) for f in ccq_facts]
        }
    
    def _compare_values(
        self,
        map_pro_facts: List[NeutralFact],
        ccq_facts: List[NeutralFact]
    ) -> Dict[str, Any]:
        """
        Compare values for facts with same concept.
        
        Args:
            map_pro_facts: Map Pro facts
            ccq_facts: CCQ facts
            
        Returns:
            Value comparison result
        """
        # Get all unique values from each system
        map_pro_values = set(f.value for f in map_pro_facts)
        ccq_values = set(f.value for f in ccq_facts)
        
        # Find matching and different values
        matching_values = map_pro_values & ccq_values
        map_pro_unique = map_pro_values - ccq_values
        ccq_unique = ccq_values - map_pro_values
        
        has_match = len(matching_values) > 0
        
        return {
            'has_matching_values': has_match,
            'matching_values': sorted(list(matching_values)),
            'map_pro_unique_values': sorted(list(map_pro_unique)),
            'ccq_unique_values': sorted(list(ccq_unique)),
            'note': self._get_value_note(has_match, map_pro_unique, ccq_unique)
        }
    
    def _get_value_note(
        self,
        has_match: bool,
        map_pro_unique: Set[str],
        ccq_unique: Set[str]
    ) -> str:
        """Generate explanatory note about value comparison."""
        if has_match and not map_pro_unique and not ccq_unique:
            return "Values match across all facts"
        elif has_match:
            return "Some values match, but each system has unique values (likely different dates/contexts)"
        else:
            return "No matching values (systems may be reporting different periods or contexts)"
    
    def _summarize_fact(self, fact: NeutralFact) -> Dict[str, Any]:
        """
        Create summary of a fact for reporting.
        
        Args:
            fact: Neutral fact
            
        Returns:
            Summary dictionary
        """
        return {
            'value': fact.value,
            'unit': fact.unit,
            'period_type': fact.period_type,
            'balance_type': fact.balance_type,
            'context_date': fact.context_date,
            'context_id': fact.context_id[:50] + '...' if len(fact.context_id) > 50 else fact.context_id
        }
    
    def _summarize_concepts(
        self,
        concept_ids: Set[str],
        facts_by_concept: Dict[str, List[NeutralFact]]
    ) -> List[Dict[str, Any]]:
        """
        Summarize a set of concepts.
        
        Args:
            concept_ids: Set of concept IDs
            facts_by_concept: Facts indexed by concept
            
        Returns:
            List of concept summaries
        """
        summaries = []
        for concept_id in sorted(concept_ids):
            facts = facts_by_concept[concept_id]
            sample = facts[0] if facts else None
            
            if sample:
                summaries.append({
                    'concept_id': concept_id,
                    'concept_namespace': sample.concept_namespace,
                    'concept_local_name': sample.concept_local_name,
                    'label': sample.label,
                    'fact_count': len(facts),
                    'sample_value': facts[0].value if facts else None,
                    'sample_date': facts[0].context_date if facts else None
                })
        
        return summaries


__all__ = ['NeutralComparator']