# File: engines/ccq_mapper/analysis/gap_pattern_analyzer.py

"""
Gap Pattern Analyzer
====================

Analyzes patterns in classification gaps.

Responsibility:
- Analyze gap type distributions
- Identify namespace patterns
- Detect property patterns
- Analyze missing properties

Note: Different from gap_pattern_detector.py which detects comprehensive patterns
in enriched gaps. This analyzer focuses on basic pattern analysis from raw gap facts.
"""

from typing import Dict, Any, List
from collections import defaultdict, Counter
from core.system_logger import get_logger

logger = get_logger(__name__)


class GapPatternAnalyzer:
    """Analyzes patterns in classification gaps."""
    
    @staticmethod
    def analyze_gap_patterns(
        gap_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze patterns in gap facts.
        
        Args:
            gap_facts: List of facts with gaps
            
        Returns:
            Pattern analysis dictionary with:
            - gap_type_counts: Count of each gap type
            - namespace_counts: Count by namespace
            - property_patterns: Common property patterns
            - most_common_gap_type: Most frequent gap type
        """
        # Count by gap type
        gap_type_counts = Counter(gf['gap_type'] for gf in gap_facts)
        
        # Count by concept namespace
        namespace_counts = Counter()
        for gap_fact in gap_facts:
            concept = gap_fact['fact'].get('concept', '')
            namespace = GapPatternAnalyzer._extract_namespace(concept)
            if namespace:
                namespace_counts[namespace] += 1
        
        # Count by property patterns
        property_patterns = Counter()
        for gap_fact in gap_facts:
            properties = gap_fact['fact'].get('extracted_properties', {})
            pattern = GapPatternAnalyzer._create_property_pattern(properties)
            property_patterns[pattern] += 1
        
        return {
            'gap_type_counts': dict(gap_type_counts),
            'namespace_counts': dict(namespace_counts),
            'property_patterns': dict(property_patterns.most_common(10)),
            'most_common_gap_type': gap_type_counts.most_common(1)[0] if gap_type_counts else None
        }
    
    @staticmethod
    def analyze_missing_properties(
        gap_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze missing properties in gap facts.
        
        Args:
            gap_facts: List of facts with gaps
            
        Returns:
            Missing properties analysis with counts for:
            - unit_ref
            - decimals
            - period_type
            - balance_type
        """
        missing_counts = defaultdict(int)
        
        for gap_fact in gap_facts:
            properties = gap_fact['fact'].get('extracted_properties', {})
            
            # Check for missing key properties
            if not properties.get('unit_ref'):
                missing_counts['unit_ref'] += 1
            if not properties.get('decimals'):
                missing_counts['decimals'] += 1
            if not properties.get('period_type'):
                missing_counts['period_type'] += 1
            if not properties.get('balance_type'):
                missing_counts['balance_type'] += 1
        
        return dict(missing_counts)
    
    @staticmethod
    def _extract_namespace(concept: str) -> str:
        """
        Extract namespace from concept.
        
        Args:
            concept: Concept string (e.g., 'us-gaap:Assets')
            
        Returns:
            Namespace prefix or 'unknown'
        """
        if ':' in concept:
            return concept.split(':', 1)[0]
        return 'unknown'
    
    @staticmethod
    def _create_property_pattern(
        properties: Dict[str, Any]
    ) -> str:
        """
        Create pattern string from properties.
        
        Args:
            properties: Properties dictionary
            
        Returns:
            Pattern string describing key property combinations
        """
        key_properties = [
            'has_unit' if properties.get('unit_ref') else 'no_unit',
            'has_decimals' if properties.get('decimals') else 'no_decimals',
            properties.get('period_type', 'unknown_period'),
            'numeric' if properties.get('is_numeric', False) else 'text'
        ]
        
        return '+'.join(key_properties)


__all__ = ['GapPatternAnalyzer']