# File: engines/ccq_mapper/analysis/performance_reporter.py

"""
Performance Reporter
====================

Generates comprehensive performance reports.

Responsibility:
- Format success metrics for reporting
- Calculate performance statistics
- Generate structured reports
"""

from typing import Dict, Any
from core.system_logger import get_logger
from .success_constants import PREFIX_ERROR

logger = get_logger(__name__)


class PerformanceReporter:
    """Generates performance reports from success metrics."""
    
    @staticmethod
    def generate_performance_report(
        success_metrics: Dict[str, Any],
        processing_time: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Args:
            success_metrics: Success metrics from SuccessCalculator
            processing_time: Time taken to process (seconds)
            
        Returns:
            Performance report dictionary with:
            - summary: High-level success summary
            - performance: Processing performance metrics
            - classification: Detailed classification metrics
            - confidence: Confidence metrics
            - clustering: Clustering metrics
            - statements: Statement metrics
            - duplicate_analysis: Duplicate analysis summary
            - recommendations: Actionable recommendations
        """
        try:
            facts_per_second = 0.0
            if processing_time > 0:
                total_facts = success_metrics.get('total_facts', 0)
                facts_per_second = total_facts / processing_time
            
            report = {
                'summary': {
                    'success_level': success_metrics.get('success_level', 'UNKNOWN'),
                    'overall_score': success_metrics.get('overall_score', 0.0),
                    'total_facts': success_metrics.get('total_facts', 0),
                    'null_quality_score': success_metrics.get('null_quality_score', 0.0),
                    'null_quality_grade': success_metrics.get('null_quality_grade', 'UNKNOWN')
                },
                'performance': {
                    'processing_time_seconds': round(processing_time, 2),
                    'facts_per_second': round(facts_per_second, 2)
                },
                'classification': success_metrics.get('classification_success', {}),
                'confidence': success_metrics.get('confidence_metrics', {}),
                'clustering': success_metrics.get('clustering_success', {}),
                'statements': success_metrics.get('statement_success', {}),
                'duplicate_analysis': success_metrics.get('duplicate_analysis', {}),
                'recommendations': success_metrics.get('recommendations', [])
            }
            
            return report
            
        except (KeyError, ValueError, TypeError, ZeroDivisionError) as e:
            logger.error(f"Performance report generation failed: {e}", exc_info=True)
            return {
                'summary': {},
                'performance': {},
                'recommendations': [
                    f"{PREFIX_ERROR} Failed to generate report: {e}"
                ]
            }


__all__ = ['PerformanceReporter']