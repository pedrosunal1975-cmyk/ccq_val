# File: engines/ccq_mapper/analysis/success_calculator.py

"""
CCQ Success Calculator
======================

Calculates comprehensive success metrics for CCQ's property-based mapper.

Purpose:
- Calculate overall mapping success rate
- Determine if processing succeeded
- Generate performance reports
- Provide actionable recommendations

Architecture: Designed for CCQ's property-based classification approach.
Unlike Map Pro's concept matching success (mapped vs unmapped),
CCQ measures classification completeness and confidence.

Success Criteria:
- >=95%: EXCELLENT (Nearly all facts well-classified)
- 90-95%: GOOD (Most facts classified, minor issues)
- 80-90%: ACCEPTABLE (Reasonable classification, needs review)
- 70-80%: POOR (Significant classification issues)
- <70%: FAILURE (Severe classification problems)

REFACTORED VERSION:
This calculator now delegates to specialized scorers and generators,
maintaining backward compatibility while improving code organization.
"""

from typing import Dict, Any, List

from core.system_logger import get_logger

# Specialized scorers (NEW)
from .classification_scorer import ClassificationScorer
from .confidence_scorer import ConfidenceScorer
from .clustering_scorer import ClusteringScorer
from .statement_scorer import StatementScorer
from .overall_scorer import OverallScorer
from .recommendation_generator import RecommendationGenerator
from .performance_reporter import PerformanceReporter

# Constants
from .success_constants import (
    SUCCESS_LEVEL_EXCELLENT,
    SUCCESS_LEVEL_GOOD,
    SUCCESS_LEVEL_ACCEPTABLE,
    ACCEPTABLE_QUALITY_SCORE
)

logger = get_logger(__name__)


class SuccessCalculationError(Exception):
    """Raised when success calculation fails."""
    pass


class SuccessCalculator:
    """
    Calculates success metrics for CCQ mapping operations.
    
    Responsibilities:
    - Calculate classification success rate
    - Determine overall processing success
    - Generate performance reports
    - Provide actionable recommendations
    
    Success Factors:
    - Classification completeness (all dimensions classified)
    - Classification confidence (high confidence scores)
    - Property extraction success (all properties extracted)
    - Clustering effectiveness (facts properly grouped)
    - Statement construction (valid statements built)
    - Null quality score (from null quality validator)
    - Duplicate detection (from duplicate detector)
    
    Does NOT:
    - Modify classifications
    - Make classification decisions
    - Access database
    """
    
    def __init__(self):
        """Initialize success calculator with specialized scorers."""
        self.logger = logger
        
        # Specialized scorers
        self.classification_scorer = ClassificationScorer()
        self.confidence_scorer = ConfidenceScorer()
        self.clustering_scorer = ClusteringScorer()
        self.statement_scorer = StatementScorer()
        self.overall_scorer = OverallScorer()
        self.recommendation_generator = RecommendationGenerator()
        self.performance_reporter = PerformanceReporter()
        
        self.logger.info("Success calculator initialized with specialized scorers")
    
    def calculate_success(
        self,
        classified_facts: List[Dict[str, Any]],
        clusters: Dict[str, List[Dict[str, Any]]],
        constructed_statements: List[Dict[str, Any]],
        classification_metrics: Dict[str, Any],
        gap_analysis: Dict[str, Any],
        null_quality_report: Dict[str, Any],
        duplicate_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive success metrics.
        
        Args:
            classified_facts: List of classified facts
            clusters: Clustered facts dictionary
            constructed_statements: Built statements
            classification_metrics: Classification metrics from ClassificationMetrics
            gap_analysis: Gap analysis from GapAnalyzer
            null_quality_report: Null quality report from NullQualityValidator
            duplicate_report: Duplicate analysis from DuplicateDetector
            
        Returns:
            Success metrics dictionary with:
            - total_facts: Total number of facts
            - classification_success: Classification metrics
            - confidence_metrics: Confidence metrics
            - clustering_success: Clustering metrics
            - statement_success: Statement metrics
            - null_quality_score: Null quality score (0-100)
            - null_quality_grade: Null quality grade
            - duplicate_analysis: Duplicate analysis summary
            - overall_score: Overall success score (0-100)
            - success_level: Success level (EXCELLENT/GOOD/ACCEPTABLE/POOR/FAILURE)
            - is_success: Boolean indicating overall success
            - recommendations: List of actionable recommendations
            
        Raises:
            SuccessCalculationError: If calculation fails
        """
        try:
            self.logger.info("Calculating success metrics...")
            
            total_facts = len(classified_facts)
            
            # Calculate classification success
            classification_success = self.classification_scorer.calculate_classification_success(
                classification_metrics,
                gap_analysis
            )
            
            # Calculate confidence metrics
            confidence_metrics = self.confidence_scorer.calculate_confidence_metrics(
                classified_facts
            )
            
            # Calculate clustering success
            clustering_success = self.clustering_scorer.calculate_clustering_success(
                clusters,
                total_facts
            )
            
            # Calculate statement construction success
            statement_success = self.statement_scorer.calculate_statement_success(
                constructed_statements
            )
            
            # Extract null quality score
            null_quality_score = null_quality_report.get('quality_score', {}).get('score', 100.0)
            null_quality_grade = null_quality_report.get('quality_score', {}).get('grade', 'UNKNOWN')
            
            # Extract duplicate analysis
            has_critical_duplicates = duplicate_report.get('has_critical_duplicates', False)
            has_major_duplicates = duplicate_report.get('has_major_duplicates', False)
            duplicate_percentage = duplicate_report.get('duplicate_percentage', 0.0)
            
            # Calculate overall success score
            overall_score = self.overall_scorer.calculate_overall_score(
                classification_success,
                confidence_metrics,
                clustering_success,
                statement_success,
                null_quality_score,
                has_critical_duplicates,
                has_major_duplicates
            )
            
            # Determine success level
            success_level = self.overall_scorer.determine_success_level(overall_score)
            
            # Generate recommendations
            recommendations = self.recommendation_generator.generate_recommendations(
                classification_success,
                confidence_metrics,
                gap_analysis,
                null_quality_report,
                duplicate_report
            )
            
            success_metrics = {
                'total_facts': total_facts,
                'classification_success': classification_success,
                'confidence_metrics': confidence_metrics,
                'clustering_success': clustering_success,
                'statement_success': statement_success,
                'null_quality_score': null_quality_score,
                'null_quality_grade': null_quality_grade,
                'duplicate_analysis': {
                    'has_critical_duplicates': has_critical_duplicates,
                    'has_major_duplicates': has_major_duplicates,
                    'duplicate_percentage': duplicate_percentage
                },
                'overall_score': overall_score,
                'success_level': success_level,
                'is_success': success_level in [
                    SUCCESS_LEVEL_EXCELLENT,
                    SUCCESS_LEVEL_GOOD,
                    SUCCESS_LEVEL_ACCEPTABLE
                ],
                'recommendations': recommendations
            }
            
            self.logger.info(
                f"Success calculation complete: {overall_score:.1f}/100 ({success_level})"
            )
            
            # Log critical issues
            if has_critical_duplicates:
                self.logger.error(
                    "[!] CRITICAL: Filing contains duplicate facts with material variance"
                )
            
            if null_quality_score < ACCEPTABLE_QUALITY_SCORE:
                self.logger.warning(
                    f"[!] WARNING: Low null quality score: {null_quality_score:.1f}"
                )
            
            return success_metrics
            
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Success calculation failed: {e}", exc_info=True)
            raise SuccessCalculationError(f"Failed to calculate success metrics: {e}")
    
    def generate_performance_report(
        self,
        success_metrics: Dict[str, Any],
        processing_time: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Args:
            success_metrics: Success metrics from calculate_success
            processing_time: Time taken to process (seconds)
            
        Returns:
            Performance report dictionary
        """
        return self.performance_reporter.generate_performance_report(
            success_metrics,
            processing_time
        )


__all__ = ['SuccessCalculator', 'SuccessCalculationError']