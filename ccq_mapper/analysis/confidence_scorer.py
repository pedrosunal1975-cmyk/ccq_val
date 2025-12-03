# File: engines/ccq_mapper/analysis/confidence_scorer.py

"""
Confidence Scorer
=================

Calculates confidence metrics for classified facts.

Responsibility:
- Calculate average confidence
- Categorize facts by confidence level
- Generate confidence distribution
"""

from typing import Dict, Any, List
from .success_constants import (
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD
)


class ConfidenceScorer:
    """Scores classification confidence."""
    
    @staticmethod
    def calculate_confidence_metrics(
        classified_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate confidence metrics.
        
        Args:
            classified_facts: List of classified facts
            
        Returns:
            Confidence metrics dictionary with:
            - average_confidence: Mean confidence score
            - high_confidence_count: Number of high-confidence facts
            - medium_confidence_count: Number of medium-confidence facts
            - low_confidence_count: Number of low-confidence facts
            - confidence_distribution: Percentage distribution
        """
        if not classified_facts:
            return {
                'average_confidence': 0.0,
                'high_confidence_count': 0,
                'medium_confidence_count': 0,
                'low_confidence_count': 0,
                'confidence_distribution': {
                    'high': 0.0,
                    'medium': 0.0,
                    'low': 0.0
                }
            }
        
        confidences = []
        high_count = 0
        medium_count = 0
        low_count = 0
        
        for fact in classified_facts:
            classification = fact.get('classification', {})
            confidence = classification.get('confidence_score', 1.0)
            confidences.append(confidence)
            
            if confidence >= HIGH_CONFIDENCE_THRESHOLD:
                high_count += 1
            elif confidence >= MEDIUM_CONFIDENCE_THRESHOLD:
                medium_count += 1
            else:
                low_count += 1
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        total = len(classified_facts)
        
        return {
            'average_confidence': round(avg_confidence, 4),
            'high_confidence_count': high_count,
            'medium_confidence_count': medium_count,
            'low_confidence_count': low_count,
            'confidence_distribution': {
                'high': round(high_count / total * 100, 2),
                'medium': round(medium_count / total * 100, 2),
                'low': round(low_count / total * 100, 2)
            }
        }


__all__ = ['ConfidenceScorer']