# File: engines/ccq_mapper/validation/null_quality_validator.py

"""
CCQ Null Quality Validator
===========================

Main orchestrator for CCQ's property-based null quality validation.
Coordinates all null quality components to produce null_quality.json.

Architecture:
- PropertyNullAnalyzer: Analyzes individual nulls
- PatternDetector: Detects patterns in null distribution
- NullQualityScorer: Calculates quality scores
- This class: Orchestrates workflow and generates final report

Key Difference from Map Pro:
- Map Pro: Searches for text explanations
- CCQ: Analyzes property patterns and classifications
"""

from typing import Dict, Any, List
from datetime import datetime

from core.system_logger import get_logger
from .property_null_analyzer import PropertyNullAnalyzer
from .pattern_detector import PatternDetector
from .null_quality_scorer import NullQualityScorer
from .null_quality_constants import (
    MSG_SUCCESS_NO_NULLS,
    MSG_ANOMALOUS_NULLS,
    MSG_HIGH_SUSPICION_NULLS,
    MSG_LEGITIMATE_NILS,
    MSG_EXPECTED_NULLS,
    MSG_STRUCTURAL_NULLS,
    SUSPICION_HIGH
)

logger = get_logger(__name__)


class NullQualityValidator:
    """
    Orchestrates CCQ's null quality validation workflow.
    
    Workflow:
    1. Load CCQ mapped statements
    2. Analyze each null using property-based logic
    3. Detect patterns across nulls
    4. Calculate quality score
    5. Generate null_quality.json report
    
    Output Format:
    - Same structure as Map Pro's null_quality.json
    - But generated using CCQ's property-based methodology
    """
    
    def __init__(self):
        """Initialize null quality validator with all components."""
        self.analyzer = PropertyNullAnalyzer()
        self.pattern_detector = PatternDetector()
        self.scorer = NullQualityScorer()
        self.logger = logger
        
        self.logger.info("CCQ Null Quality Validator initialized")
    
    def validate_statements(
        self,
        statements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate null quality across all mapped statements.
        
        Args:
            statements: List of CCQ mapped statement dictionaries
            
        Returns:
            Complete null quality report
        """
        self.logger.info(f"Validating null quality for {len(statements)} statements")
        
        # Initialize validation data
        validation_data = self._initialize_validation_data(statements)
        
        # Analyze all nulls
        null_analyses = self._analyze_all_nulls(statements)
        validation_data['null_analyses'] = null_analyses
        
        # Get statistics
        statistics = self.analyzer.get_statistics()
        validation_data['statistics'] = statistics
        
        # Detect patterns
        patterns = self.pattern_detector.detect_patterns(null_analyses)
        validation_data['patterns'] = patterns
        validation_data['pattern_summary'] = self.pattern_detector.get_pattern_summary()
        
        # Calculate score
        score_report = self.scorer.calculate_quality_score(
            statistics,
            patterns,
            null_analyses
        )
        validation_data['quality_score'] = score_report
        
        # Generate summary and recommendations
        validation_data['summary'] = self._generate_summary(
            statistics,
            patterns,
            score_report
        )
        validation_data['recommendations'] = self._generate_recommendations(
            statistics,
            patterns,
            score_report
        )
        
        # Add metadata
        validation_data['metadata'] = self._generate_metadata()
        
        self._log_validation_summary(validation_data)
        
        return validation_data
    
    def _initialize_validation_data(
        self,
        statements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Initialize validation data structure."""
        total_facts = sum(
            len(stmt.get('line_items', []))
            for stmt in statements
        )
        
        return {
            'validation_type': 'ccq_property_based',
            'total_statements': len(statements),
            'total_line_items': total_facts,
            'null_analyses': [],
            'statistics': {},
            'patterns': [],
            'pattern_summary': {},
            'quality_score': {},
            'summary': {},
            'recommendations': [],
            'metadata': {}
        }
    
    def _analyze_all_nulls(
        self,
        statements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze nulls across all statements.
        
        Args:
            statements: List of mapped statements
            
        Returns:
            List of null analysis dictionaries
        """
        null_analyses = []
        
        for statement in statements:
            line_items = statement.get('line_items', [])
            
            for item in line_items:
                # Each line item has its classification embedded
                classification = item.get('classification', {})
                
                # Analyze the item
                analysis = self.analyzer.analyze_classified_fact(item, classification)
                
                if analysis:
                    # Add statement context
                    analysis['statement_type'] = statement.get('statement_type')
                    null_analyses.append(analysis)
        
        return null_analyses
    
    def _generate_summary(
        self,
        statistics: Dict[str, int],
        patterns: List[Dict[str, Any]],
        score_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate human-readable summary."""
        total_nulls = statistics.get('total_nulls', 0)
        
        if total_nulls == 0:
            return {
                'status': 'success',
                'message': MSG_SUCCESS_NO_NULLS,
                'total_nulls': 0
            }
        
        # Calculate rates
        legitimate_rate = self.scorer.calculate_legitimate_rate(statistics)
        
        summary = {
            'status': 'analyzed',
            'total_nulls': total_nulls,
            'legitimate_nils': statistics.get('legitimate_nils', 0),
            'expected_nulls': statistics.get('expected_nulls', 0),
            'structural_nulls': statistics.get('structural_nulls', 0),
            'anomalous_nulls': statistics.get('anomalous_nulls', 0),
            'legitimate_rate': legitimate_rate,
            'quality_score': score_report.get('score', 0.0),
            'quality_grade': score_report.get('grade', 'UNKNOWN'),
            'patterns_detected': len(patterns),
            'high_severity_patterns': sum(
                1 for p in patterns if p.get('severity') == 'high'
            )
        }
        
        return summary
    
    def _generate_recommendations(
        self,
        statistics: Dict[str, int],
        patterns: List[Dict[str, Any]],
        score_report: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        total_nulls = statistics.get('total_nulls', 0)
        if total_nulls == 0:
            return [MSG_SUCCESS_NO_NULLS]
        
        # Recommendation 1: Anomalous nulls
        anomalous_count = statistics.get('anomalous_nulls', 0)
        if anomalous_count > 0:
            recommendations.append(
                MSG_ANOMALOUS_NULLS.format(count=anomalous_count)
            )
        
        # Recommendation 2: High suspicion nulls
        # Count from breakdown if available
        high_suspicion = 0
        for penalty in score_report.get('breakdown', {}).get('penalties', []):
            if penalty.get('type') == 'high_suspicion_nulls':
                high_suspicion = penalty.get('count', 0)
                break
        
        if high_suspicion > 0:
            recommendations.append(
                MSG_HIGH_SUSPICION_NULLS.format(count=high_suspicion)
            )
        
        # Recommendation 3: Pattern-specific recommendations
        for pattern in patterns:
            if pattern.get('severity') == 'high':
                recommendations.append(
                    f"[PATTERN] {pattern.get('description')} - {pattern.get('recommendation')}"
                )
        
        # Recommendation 4: Positive feedback
        legitimate_nils = statistics.get('legitimate_nils', 0)
        if legitimate_nils > 0:
            recommendations.append(
                MSG_LEGITIMATE_NILS.format(count=legitimate_nils)
            )
        
        expected_nulls = statistics.get('expected_nulls', 0)
        if expected_nulls > 0:
            recommendations.append(
                MSG_EXPECTED_NULLS.format(count=expected_nulls)
            )
        
        structural_nulls = statistics.get('structural_nulls', 0)
        if structural_nulls > 0:
            recommendations.append(
                MSG_STRUCTURAL_NULLS.format(count=structural_nulls)
            )
        
        return recommendations
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate validation metadata."""
        return {
            'validation_engine': 'ccq_property_based',
            'validation_method': 'property_analysis_and_pattern_detection',
            'validated_at': datetime.now().isoformat(),
            'validator_version': '1.0.0',
            'differs_from_map_pro': True,
            'differences': [
                'Uses property-based classification instead of text-explanation search',
                'Detects null patterns and clustering',
                'Correlates nulls with classification confidence',
                'Analyzes structural expectations from properties'
            ]
        }
    
    def _log_validation_summary(self, validation_data: Dict[str, Any]) -> None:
        """Log validation summary."""
        summary = validation_data.get('summary', {})
        score_report = validation_data.get('quality_score', {})
        
        self.logger.info(
            f"Null quality validation complete: "
            f"{summary.get('total_nulls', 0)} nulls analyzed, "
            f"score: {score_report.get('score', 0.0):.2f}, "
            f"grade: {score_report.get('grade', 'UNKNOWN')}"
        )


def create_null_quality_validator() -> NullQualityValidator:
    """
    Factory function to create null quality validator.
    
    Returns:
        Configured NullQualityValidator instance
    """
    return NullQualityValidator()


__all__ = ['NullQualityValidator', 'create_null_quality_validator']