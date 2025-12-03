"""
Fact Grouper
============

Location: ccq_val/engines/ccq_mapper/analysis/fact_grouper.py

Groups facts by concept and context for duplicate detection.

Functions:
- group_facts_by_concept_and_context: Group facts by (concept, context)
- find_duplicate_groups: Filter groups with multiple facts

Features:
- Market-agnostic fact grouping
- Efficient duplicate identification
- Handles missing concept/context gracefully
"""

from typing import Dict, Any, List, Tuple
from collections import defaultdict

from .fact_extractor import extract_concept, extract_context


def group_facts_by_concept_and_context(
    facts: List[Dict[str, Any]]
) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    """
    Group facts by (concept, context) pair.
    
    This creates the foundation for duplicate detection by identifying
    facts that share the same concept and context.
    
    Args:
        facts: List of fact dictionaries
        
    Returns:
        Dictionary mapping (concept, context) tuple to list of matching facts
    """
    groups = defaultdict(list)
    
    for fact in facts:
        concept = extract_concept(fact)
        context = extract_context(fact)
        
        # Only group facts with both concept and context
        if concept and context:
            key = (concept, context)
            groups[key].append(fact)
    
    return dict(groups)


def find_duplicate_groups(
    fact_groups: Dict[Tuple[str, str], List[Dict[str, Any]]]
) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    """
    Filter fact groups to only those with duplicates (>1 fact).
    
    Args:
        fact_groups: All fact groups from grouping
        
    Returns:
        Dictionary of only duplicate groups (groups with 2+ facts)
    """
    return {
        key: facts for key, facts in fact_groups.items()
        if len(facts) > 1
    }


def calculate_group_statistics(
    duplicate_groups: Dict[Tuple[str, str], List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Calculate statistics about duplicate groups.
    
    Args:
        duplicate_groups: Dictionary of duplicate fact groups
        
    Returns:
        Dictionary with group statistics
    """
    if not duplicate_groups:
        return {
            'total_groups': 0,
            'total_facts': 0,
            'avg_duplicates_per_group': 0.0,
            'max_duplicates_in_group': 0,
            'min_duplicates_in_group': 0
        }
    
    fact_counts = [len(facts) for facts in duplicate_groups.values()]
    total_facts = sum(fact_counts)
    
    return {
        'total_groups': len(duplicate_groups),
        'total_facts': total_facts,
        'avg_duplicates_per_group': total_facts / len(duplicate_groups),
        'max_duplicates_in_group': max(fact_counts),
        'min_duplicates_in_group': min(fact_counts)
    }