# File: engines/ccq_mapper/analysis/classification_metrics.py

"""
CCQ Classification Metrics Tracker
===================================

Tracks and analyzes classification statistics across CCQ's property-based mapping.

Purpose:
- Track classification distribution across all dimensions
- Identify classification patterns and trends
- Detect ambiguous or low-confidence classifications
- Provide detailed statistics for reporting

Architecture: Designed specifically for CCQ's multi-dimensional classification:
- Monetary type (monetary, non-monetary, ratio, etc.)
- Temporal type (instant, duration, cumulative, etc.)
- Accounting type (asset, liability, equity, revenue, expense, etc.)
- Aggregation level (line_item, subtotal, total, etc.)
- Statement type (balance_sheet, income_statement, cash_flow, other)

Unlike Map Pro's concept matching, CCQ uses property-based classification,
so metrics track classification confidence and property patterns.
"""

from typing import Dict, Any, List, Set
from collections import defaultdict, Counter

from core.system_logger import get_logger

logger = get_logger(__name__)


class ClassificationMetrics:
    """
    Tracks comprehensive classification metrics for CCQ mapper.
    
    Responsibilities:
    - Count facts by classification type
    - Track classification confidence levels
    - Identify ambiguous classifications
    - Detect classification patterns
    - Generate classification statistics report
    
    Does NOT:
    - Modify classifications
    - Make classification decisions
    - Access database
    """
    
    def __init__(self):
        """Initialize classification metrics tracker."""
        self.logger = logger
        
        # Initialize metric counters
        self.total_facts = 0
        self.classified_facts = 0
        
        # Classification dimension counters
        self.monetary_types = Counter()
        self.temporal_types = Counter()
        self.accounting_types = Counter()
        self.aggregation_levels = Counter()
        self.statement_types = Counter()
        
        # Confidence tracking
        self.low_confidence_facts = []
        self.ambiguous_facts = []
        
        # Pattern tracking
        self.property_combinations = Counter()
        
        self.logger.info("Classification metrics tracker initialized")
    
    def track_classified_facts(
        self,
        classified_facts: List[Dict[str, Any]]
    ) -> None:
        """
        Track metrics from classified facts.
        
        Args:
            classified_facts: List of facts with classifications
        """
        self.logger.info(f"Tracking metrics for {len(classified_facts)} classified facts...")
        
        self.total_facts = len(classified_facts)
        
        for fact in classified_facts:
            self._track_single_fact(fact)
        
        self.classified_facts = self.total_facts
        
        self.logger.info(
            f"Classification metrics tracked: {self.classified_facts} facts, "
            f"{len(self.low_confidence_facts)} low confidence"
        )
    
    def _track_single_fact(self, fact: Dict[str, Any]) -> None:
        """
        Track metrics from a single classified fact.
        
        Args:
            fact: Fact dictionary with classification
        """
        classification = fact.get('classification', {})
        
        if not classification:
            return
        
        # Track each classification dimension
        monetary_type = classification.get('monetary_type')
        if monetary_type:
            self.monetary_types[monetary_type] += 1
        
        temporal_type = classification.get('temporal_type')
        if temporal_type:
            self.temporal_types[temporal_type] += 1
        
        accounting_type = classification.get('accounting_type')
        if accounting_type:
            self.accounting_types[accounting_type] += 1
        
        aggregation_level = classification.get('aggregation_level')
        if aggregation_level:
            self.aggregation_levels[aggregation_level] += 1
        
        statement_type = classification.get('predicted_statement')
        if statement_type:
            self.statement_types[statement_type] += 1
        
        # Track property combination pattern
        pattern = self._create_classification_pattern(classification)
        self.property_combinations[pattern] += 1
        
        # Track confidence issues
        self._track_confidence(fact, classification)
    
    def _create_classification_pattern(
        self,
        classification: Dict[str, Any]
    ) -> str:
        """
        Create pattern string from classification.
        
        Args:
            classification: Classification dictionary
            
        Returns:
            Pattern string (e.g., "monetary+instant+asset+line_item+balance_sheet")
        """
        parts = [
            classification.get('monetary_type', 'unknown'),
            classification.get('temporal_type', 'unknown'),
            classification.get('accounting_type', 'unknown'),
            classification.get('aggregation_level', 'unknown'),
            classification.get('predicted_statement', 'unknown')
        ]
        
        return '+'.join(parts)
    
    def _track_confidence(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> None:
        """
        Track classification confidence issues.
        
        Args:
            fact: Fact dictionary
            classification: Classification dictionary
        """
        # Check for confidence scores in classification
        confidence_score = classification.get('confidence_score', 1.0)
        
        # Low confidence threshold
        if confidence_score < 0.7:
            self.low_confidence_facts.append({
                'concept': fact.get('concept', 'unknown'),
                'classification': classification,
                'confidence': confidence_score
            })
        
        # Check for ambiguous classifications
        # (e.g., multiple possible statement types)
        is_ambiguous = classification.get('is_ambiguous', False)
        if is_ambiguous:
            self.ambiguous_facts.append({
                'concept': fact.get('concept', 'unknown'),
                'classification': classification
            })
    
    def generate_metrics_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive classification metrics report.
        
        Returns:
            Metrics report dictionary
        """
        self.logger.info("Generating classification metrics report...")
        
        report = {
            'summary': self._generate_summary(),
            'distribution': self._generate_distribution(),
            'patterns': self._generate_pattern_analysis(),
            'confidence': self._generate_confidence_analysis(),
            'statistics': self._generate_statistics()
        }
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        return {
            'total_facts': self.total_facts,
            'classified_facts': self.classified_facts,
            'classification_rate': (
                round(self.classified_facts / self.total_facts * 100, 2)
                if self.total_facts > 0 else 0.0
            ),
            'low_confidence_count': len(self.low_confidence_facts),
            'ambiguous_count': len(self.ambiguous_facts)
        }
    
    def _generate_distribution(self) -> Dict[str, Any]:
        """Generate classification distribution breakdown."""
        return {
            'monetary_types': dict(self.monetary_types),
            'temporal_types': dict(self.temporal_types),
            'accounting_types': dict(self.accounting_types),
            'aggregation_levels': dict(self.aggregation_levels),
            'statement_types': dict(self.statement_types)
        }
    
    def _generate_pattern_analysis(self) -> Dict[str, Any]:
        """Generate classification pattern analysis."""
        # Get top 10 most common patterns
        top_patterns = self.property_combinations.most_common(10)
        
        # Calculate pattern diversity
        unique_patterns = len(self.property_combinations)
        
        return {
            'unique_patterns': unique_patterns,
            'top_patterns': [
                {
                    'pattern': pattern,
                    'count': count,
                    'percentage': round(count / self.total_facts * 100, 2)
                }
                for pattern, count in top_patterns
            ],
            'pattern_diversity': (
                'high' if unique_patterns > 50 else
                'medium' if unique_patterns > 20 else
                'low'
            )
        }
    
    def _generate_confidence_analysis(self) -> Dict[str, Any]:
        """Generate confidence analysis."""
        return {
            'low_confidence_facts': self.low_confidence_facts[:20],  # First 20
            'low_confidence_rate': (
                round(len(self.low_confidence_facts) / self.total_facts * 100, 2)
                if self.total_facts > 0 else 0.0
            ),
            'ambiguous_facts': self.ambiguous_facts[:20],  # First 20
            'ambiguous_rate': (
                round(len(self.ambiguous_facts) / self.total_facts * 100, 2)
                if self.total_facts > 0 else 0.0
            )
        }
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate general statistics."""
        return {
            'most_common_monetary': self._get_most_common(self.monetary_types),
            'most_common_temporal': self._get_most_common(self.temporal_types),
            'most_common_accounting': self._get_most_common(self.accounting_types),
            'most_common_aggregation': self._get_most_common(self.aggregation_levels),
            'most_common_statement': self._get_most_common(self.statement_types)
        }
    
    def _get_most_common(self, counter: Counter) -> Dict[str, Any]:
        """
        Get most common item from counter.
        
        Args:
            counter: Counter object
            
        Returns:
            Dictionary with type and count
        """
        if not counter:
            return {'type': None, 'count': 0}
        
        most_common = counter.most_common(1)[0]
        return {
            'type': most_common[0],
            'count': most_common[1],
            'percentage': round(most_common[1] / self.total_facts * 100, 2)
        }
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get current statistics summary.
        
        Returns:
            Dictionary with key statistics
        """
        return {
            'total_facts': self.total_facts,
            'classified_facts': self.classified_facts,
            'low_confidence_count': len(self.low_confidence_facts),
            'ambiguous_count': len(self.ambiguous_facts),
            'unique_patterns': len(self.property_combinations)
        }


__all__ = ['ClassificationMetrics']