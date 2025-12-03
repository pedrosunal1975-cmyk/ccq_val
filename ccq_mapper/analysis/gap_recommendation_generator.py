# File: engines/ccq_mapper/analysis/gap_recommendation_generator.py

"""
Gap Recommendation Generator
=============================

Generates actionable recommendations based on gap analysis.

Responsibility:
- Generate recommendations from gap patterns
- Generate recommendations from missing properties
- Prioritize recommendations by severity
- Format recommendations with severity prefixes

Severity Levels:
- [CRITICAL]: Severe issues requiring immediate attention
- [HIGH]: Important issues to address
- [MEDIUM]: Issues to review
- [INFO]: Informational findings
- [PATTERN]: Pattern-based insights
- [SUCCESS]: Positive findings
"""

from typing import Dict, Any, List


class GapRecommendationGenerator:
    """Generates actionable recommendations for gap analysis."""
    
    # Thresholds
    SIGNIFICANT_PATTERN_THRESHOLD = 5  # At least 5 occurrences
    HIGH_PATTERN_PERCENTAGE = 20.0     # 20% of unclassified facts
    
    # Severity prefixes
    PREFIX_CRITICAL = "[CRITICAL]"
    PREFIX_HIGH = "[HIGH]"
    PREFIX_MEDIUM = "[MEDIUM]"
    PREFIX_INFO = "[INFO]"
    PREFIX_PATTERN = "[PATTERN]"
    PREFIX_SUCCESS = "[SUCCESS]"
    
    @staticmethod
    def generate_recommendations(
        patterns: Dict[str, Any],
        missing_properties: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations based on gap analysis.
        
        Recommendations are ordered by severity:
        1. CRITICAL: Missing classifications
        2. HIGH: Incomplete classifications
        3. MEDIUM: Low confidence classifications
        4. INFO: Missing properties
        5. PATTERN: Namespace patterns
        
        Args:
            patterns: Pattern analysis results
            missing_properties: Missing properties analysis
            
        Returns:
            List of recommendation strings with severity prefixes
        """
        recommendations = []
        
        # 1. CRITICAL: Recommendations based on gap types
        gap_type_counts = patterns.get('gap_type_counts', {})
        
        if gap_type_counts.get('missing_classification', 0) > 0:
            count = gap_type_counts['missing_classification']
            recommendations.append(
                f"{GapRecommendationGenerator.PREFIX_CRITICAL} {count} facts not classified - "
                "review property extraction logic"
            )
        
        # 2. HIGH: Incomplete classifications
        if gap_type_counts.get('incomplete_classification', 0) > 0:
            count = gap_type_counts['incomplete_classification']
            recommendations.append(
                f"{GapRecommendationGenerator.PREFIX_HIGH} {count} facts incompletely classified - "
                "enhance classification rules"
            )
        
        # 3. MEDIUM: Low confidence
        if gap_type_counts.get('low_confidence', 0) > 0:
            count = gap_type_counts['low_confidence']
            recommendations.append(
                f"{GapRecommendationGenerator.PREFIX_MEDIUM} {count} low-confidence classifications - "
                "review ambiguous property patterns"
            )
        
        # 4. INFO: Missing properties
        if missing_properties.get('unit_ref', 0) > GapRecommendationGenerator.SIGNIFICANT_PATTERN_THRESHOLD:
            count = missing_properties['unit_ref']
            recommendations.append(
                f"{GapRecommendationGenerator.PREFIX_INFO} {count} facts missing unit information - "
                "may affect monetary classification"
            )
        
        if missing_properties.get('period_type', 0) > GapRecommendationGenerator.SIGNIFICANT_PATTERN_THRESHOLD:
            count = missing_properties['period_type']
            recommendations.append(
                f"{GapRecommendationGenerator.PREFIX_INFO} {count} facts missing period type - "
                "may affect temporal classification"
            )
        
        # 5. PATTERN: Namespace patterns
        namespace_counts = patterns.get('namespace_counts', {})
        total_gaps = sum(namespace_counts.values())
        
        for namespace, count in namespace_counts.items():
            percentage = (count / total_gaps * 100) if total_gaps > 0 else 0
            if percentage > GapRecommendationGenerator.HIGH_PATTERN_PERCENTAGE:
                recommendations.append(
                    f"{GapRecommendationGenerator.PREFIX_PATTERN} {namespace} namespace has {count} gaps "
                    f"({percentage:.1f}%) - consider adding namespace-specific classification rules"
                )
        
        return recommendations
    
    @staticmethod
    def generate_success_recommendation() -> str:
        """Generate success recommendation for zero gaps."""
        return f"{GapRecommendationGenerator.PREFIX_SUCCESS} No classification gaps detected"


__all__ = ['GapRecommendationGenerator']