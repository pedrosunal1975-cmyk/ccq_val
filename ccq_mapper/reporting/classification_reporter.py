# File: engines/ccq_mapper/reporting/classification_reporter.py

"""
CCQ Classification Reporter
============================

Reports classification results in human-readable format for analysis.

Purpose:
- Format classification metrics for display
- Generate classification distribution reports
- Display confidence analysis
- Report classification patterns

Architecture: Market-agnostic reporting for CCQ's property-based classification.
"""

from typing import Dict, Any, List

from core.system_logger import get_logger
from .constants import (
    SECTION_SEPARATOR,
    SUBSECTION_SEPARATOR,
    MAX_DISPLAY_ITEMS,
    MAX_DISPLAY_PATTERNS,
    CLASSIFICATION_DIMENSIONS,
    TEMPLATE_CLASSIFICATION_SUMMARY,
    DISPLAY_PRECISION
)

logger = get_logger(__name__)


class ClassificationReporter:
    """
    Reports classification metrics in human-readable format.
    
    Responsibilities:
    - Format classification statistics
    - Display dimension distributions
    - Report confidence analysis
    - Show classification patterns
    
    Does NOT:
    - Modify classifications
    - Perform calculations
    - Access database
    """
    
    def __init__(self):
        """Initialize classification reporter."""
        self.logger = logger
        self.logger.info("Classification reporter initialized")
    
    def report_classification_metrics(
        self,
        metrics_report: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable classification metrics report.
        
        Args:
            metrics_report: Classification metrics from ClassificationMetrics
            
        Returns:
            Formatted report string
        """
        self.logger.info("Generating classification metrics report...")
        
        report_lines = []
        
        # Header
        report_lines.append(SECTION_SEPARATOR)
        report_lines.append("CLASSIFICATION METRICS REPORT")
        report_lines.append(SECTION_SEPARATOR)
        report_lines.append("")
        
        # Summary section
        report_lines.extend(self._format_summary(metrics_report.get('summary', {})))
        report_lines.append("")
        
        # Distribution section
        report_lines.extend(self._format_distribution(metrics_report.get('distribution', {})))
        report_lines.append("")
        
        # Pattern analysis section
        report_lines.extend(self._format_patterns(metrics_report.get('patterns', {})))
        report_lines.append("")
        
        # Confidence analysis section
        report_lines.extend(self._format_confidence(metrics_report.get('confidence', {})))
        report_lines.append("")
        
        # Statistics section
        report_lines.extend(self._format_statistics(metrics_report.get('statistics', {})))
        
        report_lines.append("")
        report_lines.append(SECTION_SEPARATOR)
        
        report_text = "\n".join(report_lines)
        
        self.logger.info("Classification metrics report generated")
        
        return report_text
    
    def _format_summary(self, summary: Dict[str, Any]) -> List[str]:
        """
        Format classification summary section.
        
        Args:
            summary: Summary statistics
            
        Returns:
            List of formatted lines
        """
        lines = []
        lines.append(SUBSECTION_SEPARATOR)
        lines.append("CLASSIFICATION SUMMARY")
        lines.append(SUBSECTION_SEPARATOR)
        
        total = summary.get('total_facts', 0)
        classified = summary.get('classified_facts', 0)
        rate = summary.get('classification_rate', 0.0)
        
        lines.append(TEMPLATE_CLASSIFICATION_SUMMARY.format(
            classified=classified,
            total=total,
            rate=rate
        ))
        
        low_conf = summary.get('low_confidence_count', 0)
        ambiguous = summary.get('ambiguous_count', 0)
        
        if low_conf > 0:
            lines.append(f"Low Confidence Facts: {low_conf}")
        
        if ambiguous > 0:
            lines.append(f"Ambiguous Classifications: {ambiguous}")
        
        return lines
    
    def _format_distribution(self, distribution: Dict[str, Any]) -> List[str]:
        """
        Format classification distribution section.
        
        Args:
            distribution: Classification distribution data
            
        Returns:
            List of formatted lines
        """
        lines = []
        lines.append(SUBSECTION_SEPARATOR)
        lines.append("CLASSIFICATION DISTRIBUTION")
        lines.append(SUBSECTION_SEPARATOR)
        
        for dim_key, dim_label in CLASSIFICATION_DIMENSIONS.items():
            dim_data = distribution.get(f"{dim_key}s" if not dim_key.endswith('_type') else dim_key + 's', {})
            
            if not dim_data:
                continue
            
            lines.append(f"\n{dim_label}:")
            
            # Sort by count descending
            sorted_items = sorted(dim_data.items(), key=lambda x: x[1], reverse=True)
            
            for item_type, count in sorted_items[:MAX_DISPLAY_ITEMS]:
                lines.append(f"  {item_type}: {count}")
        
        return lines
    
    def _format_patterns(self, patterns: Dict[str, Any]) -> List[str]:
        """
        Format classification pattern analysis.
        
        Args:
            patterns: Pattern analysis data
            
        Returns:
            List of formatted lines
        """
        lines = []
        lines.append(SUBSECTION_SEPARATOR)
        lines.append("CLASSIFICATION PATTERNS")
        lines.append(SUBSECTION_SEPARATOR)
        
        unique = patterns.get('unique_patterns', 0)
        diversity = patterns.get('pattern_diversity', 'unknown')
        
        lines.append(f"Unique Patterns: {unique} ({diversity} diversity)")
        
        top_patterns = patterns.get('top_patterns', [])
        
        if top_patterns:
            lines.append("\nTop Classification Patterns:")
            
            for idx, pattern_data in enumerate(top_patterns[:MAX_DISPLAY_PATTERNS], 1):
                pattern = pattern_data.get('pattern', 'unknown')
                count = pattern_data.get('count', 0)
                percentage = pattern_data.get('percentage', 0.0)
                
                lines.append(f"  {idx}. {pattern}")
                lines.append(f"     Count: {count} ({percentage:.{DISPLAY_PRECISION['percentage']}f}%)")
        
        return lines
    
    def _format_confidence(self, confidence: Dict[str, Any]) -> List[str]:
        """
        Format confidence analysis section.
        
        Args:
            confidence: Confidence analysis data
            
        Returns:
            List of formatted lines
        """
        lines = []
        lines.append(SUBSECTION_SEPARATOR)
        lines.append("CONFIDENCE ANALYSIS")
        lines.append(SUBSECTION_SEPARATOR)
        
        low_conf_rate = confidence.get('low_confidence_rate', 0.0)
        ambiguous_rate = confidence.get('ambiguous_rate', 0.0)
        
        lines.append(f"Low Confidence Rate: {low_conf_rate:.{DISPLAY_PRECISION['percentage']}f}%")
        lines.append(f"Ambiguous Classification Rate: {ambiguous_rate:.{DISPLAY_PRECISION['percentage']}f}%")
        
        low_conf_facts = confidence.get('low_confidence_facts', [])
        
        if low_conf_facts:
            lines.append(f"\nLow Confidence Facts (showing first {len(low_conf_facts)}):")
            
            for fact in low_conf_facts[:MAX_DISPLAY_ITEMS]:
                concept = fact.get('concept', 'unknown')
                conf_score = fact.get('confidence', 0.0)
                lines.append(f"  - {concept}: {conf_score:.{DISPLAY_PRECISION['confidence']}f}")
        
        return lines
    
    def _format_statistics(self, statistics: Dict[str, Any]) -> List[str]:
        """
        Format general statistics section.
        
        Args:
            statistics: Statistics data
            
        Returns:
            List of formatted lines
        """
        lines = []
        lines.append(SUBSECTION_SEPARATOR)
        lines.append("CLASSIFICATION STATISTICS")
        lines.append(SUBSECTION_SEPARATOR)
        
        for stat_key, stat_label in CLASSIFICATION_DIMENSIONS.items():
            most_common_key = f"most_common_{stat_key.replace('_type', '').replace('predicted_', '')}"
            most_common = statistics.get(most_common_key, {})
            
            if most_common and most_common.get('type'):
                stat_type = most_common.get('type')
                count = most_common.get('count', 0)
                percentage = most_common.get('percentage', 0.0)
                
                lines.append(f"\nMost Common {stat_label}:")
                lines.append(f"  Type: {stat_type}")
                lines.append(f"  Count: {count} ({percentage:.{DISPLAY_PRECISION['percentage']}f}%)")
        
        return lines
    
    def log_classification_summary(
        self,
        metrics_report: Dict[str, Any]
    ) -> None:
        """
        Log classification summary to logger.
        
        Args:
            metrics_report: Classification metrics report
        """
        summary = metrics_report.get('summary', {})
        
        total = summary.get('total_facts', 0)
        classified = summary.get('classified_facts', 0)
        rate = summary.get('classification_rate', 0.0)
        
        self.logger.info(
            f"Classification complete: {classified}/{total} facts "
            f"({rate:.{DISPLAY_PRECISION['percentage']}f}%)"
        )
        
        low_conf = summary.get('low_confidence_count', 0)
        if low_conf > 0:
            self.logger.warning(f"Low confidence classifications: {low_conf}")
        
        ambiguous = summary.get('ambiguous_count', 0)
        if ambiguous > 0:
            self.logger.warning(f"Ambiguous classifications: {ambiguous}")


__all__ = ['ClassificationReporter']