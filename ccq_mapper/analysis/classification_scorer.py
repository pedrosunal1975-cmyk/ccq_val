# File: engines/ccq_mapper/analysis/classification_scorer.py

"""
Classification Scorer
=====================

Calculates classification success metrics.

Responsibility:
- Calculate classification completeness
- Analyze classification rates
- Compute classification quality scores
"""

from typing import Dict, Any


class ClassificationScorer:
    """Scores classification effectiveness."""
    
    @staticmethod
    def calculate_classification_success(
        classification_metrics: Dict[str, Any],
        gap_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate classification success metrics.
        
        Args:
            classification_metrics: Classification metrics
            gap_analysis: Gap analysis results
            
        Returns:
            Classification success dictionary with:
            - total_facts: Total number of facts
            - classified_facts: Number of classified facts
            - classification_rate: Percentage classified
            - gap_count: Number of gaps
            - gap_percentage: Percentage of gaps
            - completeness_score: Overall completeness (100 - gap_percentage)
        """
        summary = classification_metrics.get('summary', {})
        
        total_facts = summary.get('total_facts', 0)
        classified_facts = summary.get('classified_facts', 0)
        
        classification_rate = (
            classified_facts / total_facts * 100 
            if total_facts > 0 else 0.0
        )
        
        gap_count = gap_analysis.get('gap_count', 0)
        gap_percentage = gap_analysis.get('gap_percentage', 0.0)
        
        return {
            'total_facts': total_facts,
            'classified_facts': classified_facts,
            'classification_rate': round(classification_rate, 2),
            'gap_count': gap_count,
            'gap_percentage': gap_percentage,
            'completeness_score': round(100.0 - gap_percentage, 2)
        }


__all__ = ['ClassificationScorer']