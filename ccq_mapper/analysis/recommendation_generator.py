# File: engines/ccq_mapper/analysis/recommendation_generator.py

"""
Recommendation Generator
========================

Generates actionable recommendations based on success metrics.

Responsibility:
- Analyze success metrics
- Generate prioritized recommendations
- Format recommendations with severity levels
"""

from typing import Dict, Any, List
from .success_constants import (
    PREFIX_SUCCESS,
    PREFIX_INFO,
    PREFIX_WARNING,
    PREFIX_ERROR,
    MEDIUM_CONFIDENCE_THRESHOLD,
    MIN_CLASSIFICATION_COMPLETENESS
)


class RecommendationGenerator:
    """Generates actionable recommendations."""
    
    @staticmethod
    def generate_recommendations(
        classification_success: Dict[str, Any],
        confidence_metrics: Dict[str, Any],
        gap_analysis: Dict[str, Any],
        null_quality_report: Dict[str, Any],
        duplicate_report: Dict[str, Any]
    ) -> List[str]:
        """
        Generate actionable recommendations.
        
        Recommendations are ordered by priority:
        1. Critical duplicate issues (highest priority)
        2. Major duplicate issues
        3. Classification completeness issues
        4. Confidence issues
        5. Gap analysis insights
        6. Null quality issues
        7. Success acknowledgments
        
        Args:
            classification_success: Classification metrics
            confidence_metrics: Confidence metrics
            gap_analysis: Gap analysis results
            null_quality_report: Null quality report
            duplicate_report: Duplicate analysis report
            
        Returns:
            List of recommendation strings with severity prefixes
        """
        recommendations = []
        
        # 1. CRITICAL: Duplicate recommendations (HIGHEST PRIORITY)
        recommendations.extend(
            RecommendationGenerator._generate_duplicate_recommendations(duplicate_report)
        )
        
        # 2. Classification completeness recommendations
        recommendations.extend(
            RecommendationGenerator._generate_classification_recommendations(
                classification_success
            )
        )
        
        # 3. Confidence recommendations
        recommendations.extend(
            RecommendationGenerator._generate_confidence_recommendations(confidence_metrics)
        )
        
        # 4. Gap analysis recommendations (top 3)
        gap_recommendations = gap_analysis.get('recommendations', [])
        recommendations.extend(gap_recommendations[:3])
        
        # 5. Null quality recommendations (first one)
        null_recommendations = null_quality_report.get('recommendations', [])
        if null_recommendations:
            recommendations.append(null_recommendations[0])
        
        return recommendations
    
    @staticmethod
    def _generate_duplicate_recommendations(
        duplicate_report: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for duplicate issues."""
        recommendations = []
        
        if duplicate_report.get('has_critical_duplicates'):
            recommendations.append(
                f"{PREFIX_ERROR} CRITICAL DATA INTEGRITY ISSUE: Filing contains duplicate "
                "facts with material variance. RECOMMEND EXCLUSION from financial analysis."
            )
        elif duplicate_report.get('has_major_duplicates'):
            recommendations.append(
                f"{PREFIX_WARNING} Filing contains duplicate facts with significant variance. "
                "Manual review strongly recommended."
            )
        
        return recommendations
    
    @staticmethod
    def _generate_classification_recommendations(
        classification_success: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for classification issues."""
        recommendations = []
        
        completeness_score = classification_success.get('completeness_score', 0.0)
        
        if completeness_score < MIN_CLASSIFICATION_COMPLETENESS:
            recommendations.append(
                f"{PREFIX_WARNING} Low classification completeness ({completeness_score:.1f}%). "
                "Review property extraction and classification rules."
            )
        elif completeness_score >= 95.0:
            recommendations.append(
                f"{PREFIX_SUCCESS} Excellent classification completeness ({completeness_score:.1f}%)"
            )
        
        return recommendations
    
    @staticmethod
    def _generate_confidence_recommendations(
        confidence_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for confidence issues."""
        recommendations = []
        
        avg_confidence = confidence_metrics.get('average_confidence', 0.0)
        low_confidence_count = confidence_metrics.get('low_confidence_count', 0)
        
        if avg_confidence < MEDIUM_CONFIDENCE_THRESHOLD:
            recommendations.append(
                f"{PREFIX_WARNING} Low average classification confidence ({avg_confidence:.2f}). "
                "Review ambiguous property patterns."
            )
        
        if low_confidence_count > 0:
            recommendations.append(
                f"{PREFIX_INFO} {low_confidence_count} low-confidence classifications detected. "
                "Consider manual review."
            )
        
        return recommendations


__all__ = ['RecommendationGenerator']