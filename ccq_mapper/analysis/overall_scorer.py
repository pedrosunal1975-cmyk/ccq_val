# File: engines/ccq_mapper/analysis/overall_scorer.py

"""
Overall Scorer
==============

Calculates overall success score with weighted components.

Responsibility:
- Combine component scores
- Apply weights
- Apply penalties
- Determine success level
"""

from typing import Dict, Any
from core.system_logger import get_logger
from .success_constants import (
    WEIGHT_CLASSIFICATION,
    WEIGHT_CONFIDENCE,
    WEIGHT_CLUSTERING,
    WEIGHT_STATEMENT,
    WEIGHT_NULL_QUALITY,
    CRITICAL_DUPLICATE_PENALTY,
    MAJOR_DUPLICATE_PENALTY,
    EXCELLENT_THRESHOLD,
    GOOD_THRESHOLD,
    ACCEPTABLE_THRESHOLD,
    POOR_THRESHOLD,
    SUCCESS_LEVEL_EXCELLENT,
    SUCCESS_LEVEL_GOOD,
    SUCCESS_LEVEL_ACCEPTABLE,
    SUCCESS_LEVEL_POOR,
    SUCCESS_LEVEL_FAILURE
)

logger = get_logger(__name__)


class OverallScorer:
    """Calculates overall success score from components."""
    
    @staticmethod
    def calculate_overall_score(
        classification_success: Dict[str, Any],
        confidence_metrics: Dict[str, Any],
        clustering_success: Dict[str, Any],
        statement_success: Dict[str, Any],
        null_quality_score: float,
        has_critical_duplicates: bool,
        has_major_duplicates: bool
    ) -> float:
        """
        Calculate overall success score (0-100).
        
        Weighted scoring:
        - Classification completeness: 30%
        - Classification confidence: 25%
        - Clustering effectiveness: 15%
        - Statement completeness: 15%
        - Null quality: 10%
        - Duplicate penalty: -5 to -20 points
        
        Args:
            classification_success: Classification metrics
            confidence_metrics: Confidence metrics
            clustering_success: Clustering metrics
            statement_success: Statement metrics
            null_quality_score: Null quality score (0-100)
            has_critical_duplicates: Whether critical duplicates exist
            has_major_duplicates: Whether major duplicates exist
            
        Returns:
            Overall score (0-100)
        """
        # Component scores
        classification_score = classification_success.get('completeness_score', 0.0)
        confidence_score = confidence_metrics.get('average_confidence', 0.0) * 100
        clustering_score = clustering_success.get('clustering_rate', 0.0)
        statement_score = statement_success.get('completeness_percentage', 0.0)
        
        # Weighted average
        overall = (
            classification_score * WEIGHT_CLASSIFICATION +
            confidence_score * WEIGHT_CONFIDENCE +
            clustering_score * WEIGHT_CLUSTERING +
            statement_score * WEIGHT_STATEMENT +
            null_quality_score * WEIGHT_NULL_QUALITY
        )
        
        # Apply duplicate penalty
        if has_critical_duplicates:
            overall -= CRITICAL_DUPLICATE_PENALTY
            logger.warning(
                f"Applied -{CRITICAL_DUPLICATE_PENALTY} point penalty for critical duplicates"
            )
        elif has_major_duplicates:
            overall -= MAJOR_DUPLICATE_PENALTY
            logger.warning(
                f"Applied -{MAJOR_DUPLICATE_PENALTY} point penalty for major duplicates"
            )
        
        # Ensure score is within 0-100
        return max(0.0, min(100.0, round(overall, 2)))
    
    @staticmethod
    def determine_success_level(overall_score: float) -> str:
        """
        Determine success level from overall score.
        
        Args:
            overall_score: Overall score (0-100)
            
        Returns:
            Success level string (EXCELLENT, GOOD, ACCEPTABLE, POOR, FAILURE)
        """
        score_ratio = overall_score / 100
        
        if score_ratio >= EXCELLENT_THRESHOLD:
            return SUCCESS_LEVEL_EXCELLENT
        elif score_ratio >= GOOD_THRESHOLD:
            return SUCCESS_LEVEL_GOOD
        elif score_ratio >= ACCEPTABLE_THRESHOLD:
            return SUCCESS_LEVEL_ACCEPTABLE
        elif score_ratio >= POOR_THRESHOLD:
            return SUCCESS_LEVEL_POOR
        else:
            return SUCCESS_LEVEL_FAILURE


__all__ = ['OverallScorer']