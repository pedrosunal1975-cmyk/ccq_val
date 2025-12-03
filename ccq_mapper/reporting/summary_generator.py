# File: engines/ccq_mapper/reporting/summary_generator.py

"""
CCQ Summary Generator
=====================

Generates executive summaries of CCQ mapping runs for quick assessment.

Purpose:
- Create concise mapping run summaries
- Highlight critical issues and warnings
- Provide actionable recommendations
- Format for both logging and file output

Architecture: Market-agnostic summary generation for all XBRL sources.
"""

from typing import Dict, Any, List
from datetime import datetime

from core.system_logger import get_logger
from .constants import (
    SECTION_SEPARATOR,
    SUBSECTION_SEPARATOR,
    SUCCESS_LEVEL_SYMBOLS,
    MSG_SUCCESS_EXCELLENT,
    MSG_SUCCESS_GOOD,
    MSG_SUCCESS_ACCEPTABLE,
    MSG_WARNING_LOW_CONFIDENCE,
    MSG_WARNING_GAPS_DETECTED,
    MSG_WARNING_MAJOR_DUPLICATES,
    MSG_ERROR_CRITICAL_DUPLICATES,
    MSG_ERROR_CLASSIFICATION_FAILURE,
    DISPLAY_PRECISION
)

logger = get_logger(__name__)


class SummaryGenerator:
    """
    Generates executive summaries for CCQ mapping runs.
    
    Responsibilities:
    - Create concise mapping summaries
    - Identify critical issues
    - Generate recommendations
    - Format for display and file output
    
    Does NOT:
    - Modify data
    - Perform analysis
    - Access database
    """
    
    def __init__(self):
        """Initialize summary generator."""
        self.logger = logger
        self.logger.info("Summary generator initialized")
    
    def generate_executive_summary(
        self,
        filing_id: str,
        success_metrics: Dict[str, Any],
        classification_metrics: Dict[str, Any],
        duplicate_report: Dict[str, Any],
        gap_analysis: Dict[str, Any],
        null_quality_report: Dict[str, Any]
    ) -> str:
        """
        Generate executive summary of mapping run.
        
        Args:
            filing_id: Filing identifier
            success_metrics: Overall success metrics
            classification_metrics: Classification metrics report
            duplicate_report: Duplicate detection report
            gap_analysis: Gap analysis report
            null_quality_report: Null quality report
            
        Returns:
            Formatted executive summary string
        """
        self.logger.info(f"Generating executive summary for {filing_id}...")
        
        summary_lines = []
        
        # Header
        summary_lines.extend(self._format_header(filing_id))
        summary_lines.append("")
        
        # Overall status
        summary_lines.extend(self._format_overall_status(success_metrics))
        summary_lines.append("")
        
        # Key metrics
        summary_lines.extend(self._format_key_metrics(
            success_metrics,
            classification_metrics,
            duplicate_report,
            null_quality_report
        ))
        summary_lines.append("")
        
        # Critical issues
        critical_issues = self._identify_critical_issues(
            duplicate_report,
            gap_analysis,
            null_quality_report,
            success_metrics
        )
        
        if critical_issues:
            summary_lines.extend(self._format_critical_issues(critical_issues))
            summary_lines.append("")
        
        # Warnings
        warnings = self._identify_warnings(
            classification_metrics,
            duplicate_report,
            gap_analysis,
            success_metrics
        )
        
        if warnings:
            summary_lines.extend(self._format_warnings(warnings))
            summary_lines.append("")
        
        # Recommendations
        recommendations = success_metrics.get('recommendations', [])
        if recommendations:
            summary_lines.extend(self._format_recommendations(recommendations))
            summary_lines.append("")
        
        # Footer
        summary_lines.extend(self._format_footer())
        
        summary_text = "\n".join(summary_lines)
        
        self.logger.info("Executive summary generated")
        
        return summary_text
    
    def _format_header(self, filing_id: str) -> List[str]:
        """
        Format summary header.
        
        Args:
            filing_id: Filing identifier
            
        Returns:
            List of formatted lines
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        lines = []
        lines.append(SECTION_SEPARATOR)
        lines.append("CCQ MAPPER EXECUTIVE SUMMARY")
        lines.append(SECTION_SEPARATOR)
        lines.append(f"Filing ID: {filing_id}")
        lines.append(f"Generated: {timestamp}")
        
        return lines
    
    def _format_overall_status(self, success_metrics: Dict[str, Any]) -> List[str]:
        """
        Format overall status section.
        
        Args:
            success_metrics: Success metrics dictionary
            
        Returns:
            List of formatted lines
        """
        lines = []
        lines.append(SUBSECTION_SEPARATOR)
        lines.append("OVERALL STATUS")
        lines.append(SUBSECTION_SEPARATOR)
        
        overall_score = success_metrics.get('overall_score', 0.0)
        success_level = success_metrics.get('success_level', 'UNKNOWN')
        is_success = success_metrics.get('is_success', False)
        
        symbol = SUCCESS_LEVEL_SYMBOLS.get(success_level, '?')
        
        status = "SUCCESS" if is_success else "NEEDS REVIEW"
        lines.append(f"Status: {status} {symbol}")
        lines.append(f"Overall Score: {overall_score:.{DISPLAY_PRECISION['score']}f}/100")
        lines.append(f"Quality Level: {success_level}")
        
        # Add appropriate message
        if success_level == 'EXCELLENT':
            lines.append(f"\n{MSG_SUCCESS_EXCELLENT}")
        elif success_level == 'GOOD':
            lines.append(f"\n{MSG_SUCCESS_GOOD}")
        elif success_level == 'ACCEPTABLE':
            lines.append(f"\n{MSG_SUCCESS_ACCEPTABLE}")
        elif success_level == 'POOR':
            lines.append(f"\n{MSG_ERROR_CLASSIFICATION_FAILURE}")
        else:
            lines.append(f"\n{MSG_ERROR_CLASSIFICATION_FAILURE}")
        
        return lines
    
    def _format_key_metrics(
        self,
        success_metrics: Dict[str, Any],
        classification_metrics: Dict[str, Any],
        duplicate_report: Dict[str, Any],
        null_quality_report: Dict[str, Any]
    ) -> List[str]:
        """
        Format key metrics section.
        
        Args:
            success_metrics: Success metrics
            classification_metrics: Classification metrics
            duplicate_report: Duplicate report
            null_quality_report: Null quality report
            
        Returns:
            List of formatted lines
        """
        lines = []
        lines.append(SUBSECTION_SEPARATOR)
        lines.append("KEY METRICS")
        lines.append(SUBSECTION_SEPARATOR)
        
        # Classification metrics
        classification_success = success_metrics.get('classification_success', {})
        lines.append(f"Classification Rate: {classification_success.get('classification_rate', 0.0):.{DISPLAY_PRECISION['percentage']}f}%")
        lines.append(f"Classification Completeness: {classification_success.get('completeness_score', 0.0):.{DISPLAY_PRECISION['score']}f}/100")
        
        # Confidence metrics
        confidence = success_metrics.get('confidence_metrics', {})
        lines.append(f"Average Confidence: {confidence.get('average_confidence', 0.0):.{DISPLAY_PRECISION['confidence']}f}")
        
        # Statement metrics
        statement_success = success_metrics.get('statement_success', {})
        lines.append(f"Statements Constructed: {statement_success.get('statement_count', 0)}")
        
        # Quality metrics
        null_quality_score = success_metrics.get('null_quality_score', 0.0)
        null_quality_grade = success_metrics.get('null_quality_grade', 'UNKNOWN')
        lines.append(f"Null Quality: {null_quality_score:.{DISPLAY_PRECISION['score']}f}/100 ({null_quality_grade})")
        
        # Duplicate metrics
        duplicate_analysis = success_metrics.get('duplicate_analysis', {})
        duplicate_pct = duplicate_analysis.get('duplicate_percentage', 0.0)
        lines.append(f"Duplicate Facts: {duplicate_pct:.{DISPLAY_PRECISION['percentage']}f}%")
        
        return lines
    
    def _identify_critical_issues(
        self,
        duplicate_report: Dict[str, Any],
        gap_analysis: Dict[str, Any],
        null_quality_report: Dict[str, Any],
        success_metrics: Dict[str, Any]
    ) -> List[str]:
        """
        Identify critical issues.
        
        Args:
            duplicate_report: Duplicate report
            gap_analysis: Gap analysis
            null_quality_report: Null quality report
            success_metrics: Success metrics
            
        Returns:
            List of critical issue messages
        """
        issues = []
        
        # Critical duplicates
        if duplicate_report.get('has_critical_duplicates', False):
            critical_count = duplicate_report.get('severity_counts', {}).get('CRITICAL', 0)
            issues.append(f"{MSG_ERROR_CRITICAL_DUPLICATES}: {critical_count} groups")
        
        # Poor classification
        if success_metrics.get('success_level') in ['POOR', 'FAILURE']:
            issues.append(MSG_ERROR_CLASSIFICATION_FAILURE)
        
        # Severe null quality issues
        null_quality_score = null_quality_report.get('quality_score', {}).get('score', 100.0)
        if null_quality_score < 50.0:
            issues.append(f"[ERROR] Critical null quality issues: {null_quality_score:.1f}/100")
        
        return issues
    
    def _identify_warnings(
        self,
        classification_metrics: Dict[str, Any],
        duplicate_report: Dict[str, Any],
        gap_analysis: Dict[str, Any],
        success_metrics: Dict[str, Any]
    ) -> List[str]:
        """
        Identify warnings.
        
        Args:
            classification_metrics: Classification metrics
            duplicate_report: Duplicate report
            gap_analysis: Gap analysis
            success_metrics: Success metrics
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Low confidence
        confidence = success_metrics.get('confidence_metrics', {})
        avg_confidence = confidence.get('average_confidence', 1.0)
        if avg_confidence < 0.7:
            warnings.append(f"{MSG_WARNING_LOW_CONFIDENCE}: {avg_confidence:.2f}")
        
        # Classification gaps
        gap_count = gap_analysis.get('gap_count', 0)
        if gap_count > 0:
            gap_pct = gap_analysis.get('gap_percentage', 0.0)
            warnings.append(f"{MSG_WARNING_GAPS_DETECTED}: {gap_count} facts ({gap_pct:.1f}%)")
        
        # Major duplicates
        if duplicate_report.get('has_major_duplicates', False):
            major_count = duplicate_report.get('severity_counts', {}).get('MAJOR', 0)
            warnings.append(f"{MSG_WARNING_MAJOR_DUPLICATES}: {major_count} groups")
        
        # Low completeness
        classification_success = success_metrics.get('classification_success', {})
        completeness = classification_success.get('completeness_score', 100.0)
        if completeness < 80.0:
            warnings.append(f"[WARNING] Low classification completeness: {completeness:.1f}%")
        
        return warnings
    
    def _format_critical_issues(self, issues: List[str]) -> List[str]:
        """
        Format critical issues section.
        
        Args:
            issues: List of critical issue messages
            
        Returns:
            List of formatted lines
        """
        lines = []
        lines.append(SUBSECTION_SEPARATOR)
        lines.append("CRITICAL ISSUES")
        lines.append(SUBSECTION_SEPARATOR)
        
        for issue in issues:
            lines.append(f"  {issue}")
        
        return lines
    
    def _format_warnings(self, warnings: List[str]) -> List[str]:
        """
        Format warnings section.
        
        Args:
            warnings: List of warning messages
            
        Returns:
            List of formatted lines
        """
        lines = []
        lines.append(SUBSECTION_SEPARATOR)
        lines.append("WARNINGS")
        lines.append(SUBSECTION_SEPARATOR)
        
        for warning in warnings:
            lines.append(f"  {warning}")
        
        return lines
    
    def _format_recommendations(self, recommendations: List[str]) -> List[str]:
        """
        Format recommendations section.
        
        Args:
            recommendations: List of recommendation messages
            
        Returns:
            List of formatted lines
        """
        lines = []
        lines.append(SUBSECTION_SEPARATOR)
        lines.append("RECOMMENDATIONS")
        lines.append(SUBSECTION_SEPARATOR)
        
        # Show top 10 recommendations
        for rec in recommendations[:10]:
            lines.append(f"  {rec}")
        
        if len(recommendations) > 10:
            lines.append(f"\n  ... and {len(recommendations) - 10} more recommendations")
        
        return lines
    
    def _format_footer(self) -> List[str]:
        """
        Format summary footer.
        
        Returns:
            List of formatted lines
        """
        lines = []
        lines.append(SECTION_SEPARATOR)
        lines.append("END OF EXECUTIVE SUMMARY")
        lines.append(SECTION_SEPARATOR)
        
        return lines


__all__ = ['SummaryGenerator']