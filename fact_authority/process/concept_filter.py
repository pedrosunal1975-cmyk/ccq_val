# File: engines/fact_authority/process/concept_filter.py
# Path: engines/fact_authority/process/concept_filter.py

"""
Concept Filter
==============

Filters concepts that should not be validated as financial statement items.

Market agnostic - works across all regulatory frameworks (SEC, FCA, ESMA).

Excludes:
- TextBlock concepts (disclosure blocks, not line items)
- Dimensional concepts (Axis, Domain, Member)
- Metadata concepts (counts, descriptions, percentages)
- Policy concepts (accounting policy text)
- Table concepts (tabular presentations)

Responsibilities:
    - Identify non-financial concepts
    - Filter concept lists for validation
    - Preserve all concepts in source data (no deletion)
    
Does NOT:
    - Delete concepts from source files
    - Modify concept values
    - Make statement placement decisions
"""

from typing import List, Set


class ConceptFilter:
    """
    Filters non-financial concepts from statement validation.
    
    Uses suffix, prefix, and pattern matching to identify concepts
    that should not be validated as financial statement line items.
    
    Market agnostic - patterns work across SEC, FCA, ESMA frameworks.
    """
    
    # Concepts ending with these suffixes should be excluded
    EXCLUDE_SUFFIXES: Set[str] = {
        # Disclosure blocks (entire text sections)
        'TextBlock',
        'PolicyTextBlock',
        'TableTextBlock',
        'DisclosureTextBlock',
        
        # XBRL dimensional concepts
        'Axis',
        'Domain',
        'Member',
        'LineItems',
        
        # Abstract groupings
        'Abstract',
    }
    
    # Concepts starting with these prefixes should be excluded
    EXCLUDE_PREFIXES: Set[str] = {
        # Counts and quantities (descriptive, not financial values)
        'NumberOf',
        
        # Table references
        'ScheduleOf',
    }
    
    # Concepts containing these patterns should be excluded
    EXCLUDE_PATTERNS: Set[str] = {
        # Ratios and percentages (typically in notes, not statements)
        'Percentage',
        'Percent',
        'Rate',
        
        # Time periods (metadata, not financial values)
        'Term',
        'Period',
        
        # Descriptions (text, not financial values)
        'Description',
        
        # Ownership details (in notes, not statements)
        'OwnershipPercentage',
        
        # Averages (typically disclosure details)
        'WeightedAverage',
    }
    
    @classmethod
    def should_exclude(cls, concept: str) -> bool:
        """
        Determine if concept should be excluded from statement validation.
        
        Uses pattern matching to identify non-financial concepts.
        Market agnostic - works across all regulatory frameworks.
        
        Args:
            concept: Concept QName (e.g., 'us-gaap:RevenueTextBlock')
            
        Returns:
            True if concept should be excluded from validation
            
        Examples:
            >>> ConceptFilter.should_exclude('us-gaap:RevenueTextBlock')
            True
            
            >>> ConceptFilter.should_exclude('us-gaap:Revenue')
            False
            
            >>> ConceptFilter.should_exclude('us-gaap:NumberOfCustomers')
            True
        """
        if not concept:
            return False
        
        # Extract local name (strip namespace)
        local_name = concept.split(':')[-1] if ':' in concept else concept
        
        # Check suffixes
        for suffix in cls.EXCLUDE_SUFFIXES:
            if local_name.endswith(suffix):
                return True
        
        # Check prefixes
        for prefix in cls.EXCLUDE_PREFIXES:
            if local_name.startswith(prefix):
                return True
        
        # Check patterns (anywhere in name)
        for pattern in cls.EXCLUDE_PATTERNS:
            if pattern in local_name:
                return True
        
        return False
    
    @classmethod
    def filter_concepts(cls, concepts: List[str]) -> List[str]:
        """
        Filter list of concepts to only those that should be validated.
        
        Removes non-financial concepts (TextBlocks, metadata, etc.)
        while preserving all financial statement line items.
        
        Args:
            concepts: List of concept QNames
            
        Returns:
            Filtered list containing only financial concepts
            
        Examples:
            >>> concepts = [
            ...     'us-gaap:Revenue',
            ...     'us-gaap:RevenueTextBlock',
            ...     'us-gaap:NumberOfCustomers',
            ...     'us-gaap:Assets'
            ... ]
            >>> ConceptFilter.filter_concepts(concepts)
            ['us-gaap:Revenue', 'us-gaap:Assets']
        """
        return [c for c in concepts if not cls.should_exclude(c)]
    
    @classmethod
    def get_excluded_concepts(cls, concepts: List[str]) -> List[str]:
        """
        Get list of concepts that would be excluded.
        
        Useful for logging/reporting what was filtered out.
        
        Args:
            concepts: List of concept QNames
            
        Returns:
            List of excluded concepts
        """
        return [c for c in concepts if cls.should_exclude(c)]
    
    @classmethod
    def get_filter_statistics(cls, concepts: List[str]) -> dict:
        """
        Get statistics about filtering.
        
        Args:
            concepts: List of concept QNames
            
        Returns:
            Dictionary with filtering statistics
            
        Example:
            {
                'total_concepts': 1386,
                'financial_concepts': 999,
                'excluded_concepts': 387,
                'exclusion_rate': 0.279
            }
        """
        total = len(concepts)
        excluded = [c for c in concepts if cls.should_exclude(c)]
        financial = total - len(excluded)
        
        return {
            'total_concepts': total,
            'financial_concepts': financial,
            'excluded_concepts': len(excluded),
            'exclusion_rate': len(excluded) / total if total > 0 else 0.0
        }


__all__ = ['ConceptFilter']