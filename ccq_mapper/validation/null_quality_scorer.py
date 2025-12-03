# File: engines/ccq_mapper/validation/null_quality_scorer.py

"""
CCQ Null Quality Scorer
========================

Calculates quality scores based on CCQ's property-based null analysis.
Different scoring logic from Map Pro's explanation-coverage approach.

CCQ Scoring Factors:
1. Legitimate nil rate (higher is better)
2. Anomalous null count (penalties)
3. Pattern clustering severity (penalties)
4. Classification confidence correlation (penalties/bonuses)
"""

from typing import Dict, Any, List

from core.system_logger import get_logger
from .null_quality_constants import (
    SCORE_EXCELLENT_THRESHOLD,
    SCORE_GOOD_THRESHOLD,
    SCORE_ACCEPTABLE_THRESHOLD,
    SCORE_POOR_THRESHOLD,
    PENALTY_ANOMALOUS_NULL,
    PENALTY_HIGH_SUSPICION_NULL,
    PENALTY_PATTERN_CLUSTER,
    BONUS_HIGH_LEGITIMATE_RATE,
    HIGH_LEGITIMATE_THRESHOLD,
    GRADE_EXCELLENT,
    GRADE_GOOD,
    GRADE_ACCEPTABLE,
    GRADE_POOR,
    GRADE_CRITICAL,
    SUSPICION_HIGH,
    SUSPICION_MEDIUM
)

logger = get_logger(__name__)


class NullQualityScorer:
    """
    Calculates quality scores for CCQ's null analysis.
    
    CCQ Scoring Logic:
    - Start with base score (100)
    - Deduct for anomalous nulls
    - Deduct for suspicious patterns
    - Bonus for high legitimate rate
    - Bonus for high classification confidence
    """
    
    def __init__(self):
        """Initialize null quality scorer."""
        self.base_score = 100.0
        self.logger = logger
    
    def calculate_quality_score(
        self,
        statistics: Dict[str, int],
        patterns: List[Dict[str, Any]],
        null_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive quality score.
        
        Args:
            statistics: Null analysis statistics
            patterns: Detected patterns
            null_analyses: Individual null analyses
            
        Returns:
            Score report dictionary
        """
        score = self.base_score
        score_breakdown = {
            'base_score': self.base_score,
            'penalties': [],
            'bonuses': [],
            'final_score': 0.0
        }
        
        # Apply penalties
        score, score_breakdown = self._apply_penalties(
            score, 
            score_breakdown, 
            statistics, 
            patterns, 
            null_analyses
        )
        
        # Apply bonuses
        score, score_breakdown = self._apply_bonuses(
            score, 
            score_breakdown, 
            statistics
        )
        
        # Normalize score
        final_score = self._normalize_score(score)
        score_breakdown['final_score'] = final_score
        
        # Determine grade
        grade = self._determine_grade(final_score)
        
        return {
            'score': final_score,
            'grade': grade,
            'breakdown': score_breakdown,
            'interpretation': self._interpret_score(final_score, grade)
        }
    
    def _apply_penalties(
        self,
        score: float,
        breakdown: Dict[str, Any],
        statistics: Dict[str, int],
        patterns: List[Dict[str, Any]],
        null_analyses: List[Dict[str, Any]]
    ) -> tuple:
        """Apply all penalties to score."""
        
        # Penalty 1: Anomalous nulls
        anomalous_count = statistics.get('anomalous_nulls', 0)
        if anomalous_count > 0:
            penalty = anomalous_count * PENALTY_ANOMALOUS_NULL
            score -= penalty
            breakdown['penalties'].append({
                'type': 'anomalous_nulls',
                'count': anomalous_count,
                'penalty': penalty,
                'reason': f"{anomalous_count} anomalous null values"
            })
        
        # Penalty 2: High suspicion nulls
        high_suspicion_count = sum(
            1 for analysis in null_analyses 
            if analysis.get('suspicion_level') == SUSPICION_HIGH
        )
        if high_suspicion_count > 0:
            penalty = high_suspicion_count * PENALTY_HIGH_SUSPICION_NULL
            score -= penalty
            breakdown['penalties'].append({
                'type': 'high_suspicion_nulls',
                'count': high_suspicion_count,
                'penalty': penalty,
                'reason': f"{high_suspicion_count} high-suspicion nulls"
            })
        
        # Penalty 3: Pattern clustering
        high_severity_patterns = [
            p for p in patterns 
            if p.get('severity') == 'high'
        ]
        if high_severity_patterns:
            penalty = len(high_severity_patterns) * PENALTY_PATTERN_CLUSTER
            score -= penalty
            breakdown['penalties'].append({
                'type': 'pattern_clustering',
                'count': len(high_severity_patterns),
                'penalty': penalty,
                'reason': f"{len(high_severity_patterns)} high-severity patterns detected"
            })
        
        # Penalty 4: Medium suspicion nulls (smaller penalty)
        medium_suspicion_count = sum(
            1 for analysis in null_analyses 
            if analysis.get('suspicion_level') == SUSPICION_MEDIUM
        )
        if medium_suspicion_count > 0:
            penalty = medium_suspicion_count * (PENALTY_ANOMALOUS_NULL / 2)
            score -= penalty
            breakdown['penalties'].append({
                'type': 'medium_suspicion_nulls',
                'count': medium_suspicion_count,
                'penalty': penalty,
                'reason': f"{medium_suspicion_count} medium-suspicion nulls"
            })
        
        return score, breakdown
    
    def _apply_bonuses(
        self,
        score: float,
        breakdown: Dict[str, Any],
        statistics: Dict[str, int]
    ) -> tuple:
        """Apply all bonuses to score."""
        
        total_nulls = statistics.get('total_nulls', 0)
        if total_nulls == 0:
            return score, breakdown
        
        # Bonus 1: High legitimate nil rate
        legitimate_nils = statistics.get('legitimate_nils', 0)
        legitimate_rate = (legitimate_nils / total_nulls * 100) if total_nulls > 0 else 0
        
        if legitimate_rate > HIGH_LEGITIMATE_THRESHOLD:
            bonus = BONUS_HIGH_LEGITIMATE_RATE
            score += bonus
            breakdown['bonuses'].append({
                'type': 'high_legitimate_rate',
                'rate': round(legitimate_rate, 1),
                'bonus': bonus,
                'reason': f"{legitimate_rate:.1f}% legitimate nils"
            })
        
        # Bonus 2: High expected null rate
        expected_nulls = statistics.get('expected_nulls', 0)
        expected_rate = (expected_nulls / total_nulls * 100) if total_nulls > 0 else 0
        
        if expected_rate > 50.0:
            bonus = 3
            score += bonus
            breakdown['bonuses'].append({
                'type': 'high_expected_rate',
                'rate': round(expected_rate, 1),
                'bonus': bonus,
                'reason': f"{expected_rate:.1f}% expected nulls based on properties"
            })
        
        return score, breakdown
    
    def _normalize_score(self, score: float) -> float:
        """Normalize score to 0-100 range."""
        return max(0.0, min(100.0, round(score, 2)))
    
    def _determine_grade(self, score: float) -> str:
        """Determine quality grade from score."""
        if score >= SCORE_EXCELLENT_THRESHOLD:
            return GRADE_EXCELLENT
        elif score >= SCORE_GOOD_THRESHOLD:
            return GRADE_GOOD
        elif score >= SCORE_ACCEPTABLE_THRESHOLD:
            return GRADE_ACCEPTABLE
        elif score >= SCORE_POOR_THRESHOLD:
            return GRADE_POOR
        else:
            return GRADE_CRITICAL
    
    def _interpret_score(self, score: float, grade: str) -> str:
        """Provide interpretation of the score."""
        interpretations = {
            GRADE_EXCELLENT: "Exceptional null quality - nearly all nulls are legitimate or well-explained by properties",
            GRADE_GOOD: "Good null quality - most nulls are legitimate or expected based on classification",
            GRADE_ACCEPTABLE: "Acceptable null quality - some anomalous nulls present but manageable",
            GRADE_POOR: "Poor null quality - significant anomalous nulls require review",
            GRADE_CRITICAL: "Critical null quality issues - many unexplained nulls or severe patterns detected"
        }
        
        return interpretations.get(grade, "Unable to interpret score")
    
    def calculate_legitimate_rate(self, statistics: Dict[str, int]) -> float:
        """Calculate rate of legitimate nulls."""
        total_nulls = statistics.get('total_nulls', 0)
        if total_nulls == 0:
            return 100.0
        
        legitimate = statistics.get('legitimate_nils', 0)
        expected = statistics.get('expected_nulls', 0)
        structural = statistics.get('structural_nulls', 0)
        
        legitimate_count = legitimate + expected + structural
        return round((legitimate_count / total_nulls * 100), 2)


__all__ = ['NullQualityScorer']