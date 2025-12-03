"""
Aggregation Classifier
======================

Classifies facts by their aggregation level (totals vs line items).

CRITICAL: Classifies by LABEL PATTERNS, not concept relationships.
"""

from typing import Dict, Any, List
import re


class AggregationClassifier:
    """
    Classify facts by aggregation level.
    
    Categories:
    - TOTAL: Top-level totals (Total Assets, Net Income, etc.)
    - SUBTOTAL: Mid-level subtotals (Current Assets, Operating Income, etc.)
    - LINE_ITEM: Individual line items (Cash, Revenue, etc.)
    - ABSTRACT: Non-numeric grouping labels
    - UNKNOWN: Cannot determine
    
    Uses label analysis and abstract attribute.
    """
    
    # Total indicators (strongest aggregation)
    TOTAL_PATTERNS = [
        r'\btotal\b',
        r'\bnet\b.*\b(income|loss|earnings|profit)\b',
        r'\b(income|loss|earnings)\b.*\bnet\b',
        r'\btotal.*assets\b',
        r'\btotal.*liabilities\b',
        r'\btotal.*equity\b',
        r'\bnet.*assets\b'
    ]
    
    # Subtotal indicators (mid-level aggregation)
    SUBTOTAL_PATTERNS = [
        r'\bcurrent\s+assets\b',
        r'\bcurrent\s+liabilities\b',
        r'\bnon-?current\s+assets\b',
        r'\bnon-?current\s+liabilities\b',
        r'\boperating\s+(income|expenses?)\b',
        r'\bgross\s+(profit|margin)\b',
        r'\b(short|long)-?term\s+(assets|liabilities|debt)\b',
        r'\btotal.*current\b',
        r'\btotal.*non-?current\b'
    ]
    
    # Abstract/header indicators
    ABSTRACT_PATTERNS = [
        r'^\[.*\]$',  # [Header Text]
        r'^statement\s+of\b',
        r'^\s*$'  # Empty label
    ]
    
    def classify(self, properties: Dict[str, Any]) -> str:
        """
        Classify fact by aggregation level.
        
        Args:
            properties: Extracted properties dictionary
            
        Returns:
            Classification: 'total', 'subtotal', 'line_item', 'abstract', 'unknown'
        """
        # Check if abstract
        if properties.get('is_abstract', False):
            return 'abstract'
        
        # Non-numeric values are typically abstract or informational
        value_type = (properties.get('value_type') or '').lower()
        if value_type in ['text', 'nil']:
            return 'abstract'
        
        # Analyze label
        label = properties.get('label', '')
        if not label:
            return 'unknown'
        
        label_lower = label.lower()
        
        # Check for abstract patterns
        if self._matches_patterns(label_lower, self.ABSTRACT_PATTERNS):
            return 'abstract'
        
        # Check for total patterns
        if self._matches_patterns(label_lower, self.TOTAL_PATTERNS):
            return 'total'
        
        # Check for subtotal patterns
        if self._matches_patterns(label_lower, self.SUBTOTAL_PATTERNS):
            return 'subtotal'
        
        # Check for line item indicators (more specific labels)
        if self._is_line_item_pattern(label_lower):
            return 'line_item'
        
        # Default to line item for numeric values
        if value_type == 'numeric':
            return 'line_item'
        
        return 'unknown'
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given regex patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _is_line_item_pattern(self, label: str) -> bool:
        """
        Detect if label represents a line item.
        
        Line items are typically:
        - Specific account names without aggregation words
        - Not containing "total", "subtotal", etc.
        - Concrete rather than abstract
        """
        # If it has "total" or similar, it's not a line item
        aggregation_words = ['total', 'subtotal', 'sum of', 'aggregate']
        if any(word in label for word in aggregation_words):
            return False
        
        # Line items typically have more specific terms
        return True
    
    def is_aggregated(self, properties: Dict[str, Any]) -> bool:
        """Check if fact represents an aggregated value (total or subtotal)."""
        classification = self.classify(properties)
        return classification in ['total', 'subtotal']
    
    def is_line_item(self, properties: Dict[str, Any]) -> bool:
        """Check if fact represents a line item."""
        return self.classify(properties) == 'line_item'
    
    def get_aggregation_score(self, properties: Dict[str, Any]) -> int:
        """
        Get numeric aggregation score.
        
        Higher score = higher level of aggregation
        
        Returns:
            3: Total
            2: Subtotal
            1: Line item
            0: Abstract/Unknown
        """
        classification = self.classify(properties)
        
        scores = {
            'total': 3,
            'subtotal': 2,
            'line_item': 1,
            'abstract': 0,
            'unknown': 0
        }
        
        return scores.get(classification, 0)
    
    def compare_aggregation_levels(
        self,
        props1: Dict[str, Any],
        props2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare aggregation levels of two facts.
        
        Used for building hierarchies.
        """
        score1 = self.get_aggregation_score(props1)
        score2 = self.get_aggregation_score(props2)
        
        return {
            'same_level': score1 == score2,
            'fact1_higher': score1 > score2,
            'fact2_higher': score2 > score1,
            'score1': score1,
            'score2': score2,
            'level_difference': abs(score1 - score2)
        }
    
    def detect_potential_parent(
        self,
        child_properties: Dict[str, Any],
        candidate_parent_properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze if candidate could be parent of child in hierarchy.
        
        Parent should have:
        - Higher aggregation level
        - Similar temporal properties
        - Compatible labels
        """
        comparison = self.compare_aggregation_levels(
            child_properties,
            candidate_parent_properties
        )
        
        # Parent must have higher aggregation level
        if not comparison['fact2_higher']:
            return {
                'is_potential_parent': False,
                'reason': 'Candidate does not have higher aggregation level'
            }
        
        # Check label compatibility
        child_label = (child_properties.get('label') or '').lower()
        parent_label = (candidate_parent_properties.get('label') or '').lower()
        
        # Simple heuristic: child label should not be more aggregate than parent
        if 'total' in child_label and 'total' not in parent_label:
            return {
                'is_potential_parent': False,
                'reason': 'Label hierarchy inconsistent'
            }
        
        return {
            'is_potential_parent': True,
            'confidence': 0.7,  # Could be enhanced with more analysis
            'level_difference': comparison['level_difference']
        }


__all__ = ['AggregationClassifier']