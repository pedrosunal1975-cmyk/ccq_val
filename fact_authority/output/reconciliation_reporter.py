# File: engines/fact_authority/output/reconciliation_reporter.py
# Path: engines/fact_authority/output/reconciliation_reporter.py

"""
Reconciliation Reporter
=======================

Generates comprehensive reconciliation reports.

Responsibilities:
- Aggregate statistics across all statements
- Detail discrepancies between mappers and taxonomy
- Include null quality analysis
- Include duplicate quality analysis (NEW)
- Provide actionable recommendations
- Generate executive summary

Does NOT:
- Make reconciliation decisions (reconciler does that)
- Validate statements (reconciler does that)
- Write files (output_writer does that)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from core.system_logger import get_logger

logger = get_logger(__name__)


class ReconciliationReporter:
    """
    Generates comprehensive reconciliation reports.
    
    Combines data from reconciliation, null quality analysis,
    and duplicate analysis into a unified report.
    """
    
    def __init__(self):
        """Initialize reporter."""
        self.logger = logger
    
    def generate_report(
        self,
        reconciliation_result: Dict[str, Any],
        null_quality_analysis: Dict[str, Any],
        duplicate_reports: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive reconciliation report.
        
        Args:
            reconciliation_result: Results from StatementReconciler
            null_quality_analysis: Results from NullQualityHandler
            duplicate_reports: Optional duplicate comparison from both mappers (NEW)
            
        Returns:
            Complete reconciliation report
        """
        self.logger.info("Generating reconciliation report")
        
        overall_stats = reconciliation_result.get('overall_statistics', {})
        
        report = {
            'report_metadata': {
                'report_generated_at': datetime.utcnow().isoformat() + 'Z',
                'report_version': '2.1.0',
                'engine': 'fact_authority',
                'validation_method': 'taxonomy_authority'
            },
            'executive_summary': self._generate_executive_summary(
                overall_stats,
                null_quality_analysis,
                duplicate_reports
            ),
            'overall_statistics': overall_stats,
            'statement_details': self._generate_statement_details(
                reconciliation_result.get('statements', {})
            ),
            'null_quality_analysis': null_quality_analysis,
            'discrepancies': self._extract_discrepancies(
                reconciliation_result.get('statements', {})
            ),
            'recommendations': self._generate_recommendations(
                overall_stats,
                null_quality_analysis,
                duplicate_reports
            )
        }
        
        # Add duplicate quality section if available
        if duplicate_reports:
            report['duplicate_quality'] = self._format_duplicate_quality(duplicate_reports)
        
        self.logger.info("Generated reconciliation report")
        
        return report
    
    def _generate_executive_summary(
        self,
        overall_stats: Dict[str, Any],
        null_quality_analysis: Dict[str, Any],
        duplicate_reports: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate executive summary of reconciliation.
        
        Args:
            overall_stats: Overall statistics from reconciler
            null_quality_analysis: Null quality analysis
            duplicate_reports: Optional duplicate comparison
            
        Returns:
            Executive summary dict
        """
        total = overall_stats.get('total_concepts', 0)
        correct_both = overall_stats.get('taxonomy_correct_both', 0)
        
        correctness_rate = 0.0
        if total > 0:
            correctness_rate = (correct_both / total) * 100
        
        summary = {
            'total_concepts_validated': total,
            'taxonomy_correct_both': correct_both,
            'correctness_percentage': round(correctness_rate, 1),
            'map_pro_facts': overall_stats.get('map_pro_facts', 0),
            'ccq_facts': overall_stats.get('ccq_facts', 0),
            'not_in_taxonomy': overall_stats.get('not_in_taxonomy', 0),
            'discrepancies_count': (
                overall_stats.get('taxonomy_correct_map_pro_only', 0) +
                overall_stats.get('taxonomy_correct_ccq_only', 0) +
                overall_stats.get('taxonomy_correct_neither', 0)
            ),
            'null_quality_issues': (
                null_quality_analysis.get('map_pro_null_count', 0) +
                null_quality_analysis.get('ccq_null_count', 0)
            ),
            'overall_quality': self._assess_overall_quality(correctness_rate)
        }
        
        # Add duplicate metrics if available
        if duplicate_reports:
            comparison = duplicate_reports.get('comparison', {})
            quality_assessment = duplicate_reports.get('quality_assessment', {})
            
            summary['duplicate_analysis'] = {
                'agreement_rate': comparison.get('agreement_rate', 0.0),
                'cleaner_mapper': comparison.get('cleaner_mapper', 'unknown'),
                'critical_duplicates': (
                    duplicate_reports.get('map_pro_report', {}).get('has_critical', False) or
                    duplicate_reports.get('ccq_report', {}).get('has_critical', False)
                ),
                'major_duplicates': (
                    duplicate_reports.get('map_pro_report', {}).get('has_major', False) or
                    duplicate_reports.get('ccq_report', {}).get('has_major', False)
                ),
                'overall_status': quality_assessment.get('overall_status', 'UNKNOWN')
            }
        
        return summary
    
    def _assess_overall_quality(self, correctness_rate: float) -> str:
        """
        Assess overall quality based on correctness rate.
        
        Args:
            correctness_rate: Percentage of concepts correct in both mappers
            
        Returns:
            Quality grade: EXCELLENT, GOOD, FAIR, POOR
        """
        if correctness_rate >= 90:
            return 'EXCELLENT'
        elif correctness_rate >= 80:
            return 'GOOD'
        elif correctness_rate >= 70:
            return 'FAIR'
        else:
            return 'POOR'
    
    def _generate_statement_details(
        self,
        statements: Dict[str, Dict]
    ) -> Dict[str, Dict]:
        """
        Generate detailed breakdown for each statement.
        
        Args:
            statements: Statement data from reconciler
            
        Returns:
            Dict with details for each statement type
        """
        details = {}
        
        for stmt_type, stmt_data in statements.items():
            stats = stmt_data.get('statistics', {})
            
            total = stats.get('total_concepts', 0)
            correct_both = stats.get('taxonomy_correct_both', 0)
            
            correctness_rate = 0.0
            if total > 0:
                correctness_rate = (correct_both / total) * 100
            
            details[stmt_type] = {
                'total_concepts': total,
                'taxonomy_correct_both': correct_both,
                'correctness_percentage': round(correctness_rate, 1),
                'taxonomy_correct_map_pro_only': stats.get('taxonomy_correct_map_pro_only', 0),
                'taxonomy_correct_ccq_only': stats.get('taxonomy_correct_ccq_only', 0),
                'taxonomy_correct_neither': stats.get('taxonomy_correct_neither', 0),
                'not_in_taxonomy': stats.get('not_in_taxonomy', 0),
                'map_pro_facts': stats.get('map_pro_facts', 0),
                'ccq_facts': stats.get('ccq_facts', 0)
            }
        
        return details
    
    def _extract_discrepancies(
        self,
        statements: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Extract all discrepancies across statements.
        
        Args:
            statements: Statement data from reconciler
            
        Returns:
            List of discrepancy dicts
        """
        all_discrepancies = []
        
        for stmt_type, stmt_data in statements.items():
            discrepancies = stmt_data.get('discrepancies', [])
            
            for discrepancy in discrepancies:
                all_discrepancies.append({
                    'statement': stmt_type,
                    **discrepancy
                })
        
        return all_discrepancies
    
    def _generate_recommendations(
        self,
        overall_stats: Dict[str, Any],
        null_quality_analysis: Dict[str, Any],
        duplicate_reports: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Generate actionable recommendations based on results.
        
        Args:
            overall_stats: Overall statistics
            null_quality_analysis: Null quality analysis
            duplicate_reports: Optional duplicate comparison
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        total = overall_stats.get('total_concepts', 0)
        correct_both = overall_stats.get('taxonomy_correct_both', 0)
        
        # Correctness recommendation
        correctness_rate = 0.0
        if total > 0:
            correctness_rate = (correct_both / total) * 100
        
        if correctness_rate < 80:
            recommendations.append(
                f"Correctness rate is {correctness_rate:.1f}%. "
                f"Review mapper logic to improve taxonomy compliance."
            )
        
        # Discrepancy recommendations
        map_pro_only = overall_stats.get('taxonomy_correct_map_pro_only', 0)
        ccq_only = overall_stats.get('taxonomy_correct_ccq_only', 0)
        neither = overall_stats.get('taxonomy_correct_neither', 0)
        
        if neither > 10:
            recommendations.append(
                f"Found {neither} concepts where neither mapper matches taxonomy. "
                f"These require detailed review against taxonomy rules."
            )
        
        # Mapper coverage balance
        if map_pro_only > ccq_only * 2:
            recommendations.append(
                f"Map Pro has {map_pro_only} correct concepts not in CCQ. "
                f"CCQ mapper may need tuning to improve coverage."
            )
        elif ccq_only > map_pro_only * 2:
            recommendations.append(
                f"CCQ has {ccq_only} correct concepts not in Map Pro. "
                f"Map Pro mapper may need review for concept coverage."
            )
        
        # Extension concepts
        not_in_taxonomy = overall_stats.get('not_in_taxonomy', 0)
        if not_in_taxonomy > total * 0.1:
            recommendations.append(
                f"Found {not_in_taxonomy} extension concepts not in taxonomy. "
                f"Consider validating extension concept definitions."
            )
        
        # Null quality recommendations
        common_nulls = len(null_quality_analysis.get('common_null_concepts', []))
        
        if common_nulls > 10:
            recommendations.append(
                f"Both mappers identified {common_nulls} concepts with null/quality issues. "
                f"These may indicate source data problems requiring investigation."
            )
        
        # Duplicate quality recommendations (NEW)
        if duplicate_reports:
            comparison = duplicate_reports.get('comparison', {})
            map_pro_report = duplicate_reports.get('map_pro_report', {})
            ccq_report = duplicate_reports.get('ccq_report', {})
            quality_assessment = duplicate_reports.get('quality_assessment', {})
            
            # Critical duplicates
            if map_pro_report.get('has_critical') or ccq_report.get('has_critical'):
                recommendations.append(
                    "⚠️ CRITICAL duplicates detected in mapper outputs. "
                    "Exclude these from analysis until source data is corrected."
                )
            
            # Major duplicates
            if map_pro_report.get('has_major') or ccq_report.get('has_major'):
                recommendations.append(
                    "⚠️ MAJOR duplicates detected. Review for currency conversion or rounding issues."
                )
            
            # Agreement rate
            agreement_rate = comparison.get('agreement_rate', 0)
            if agreement_rate < 85:
                recommendations.append(
                    f"Mappers agree on only {agreement_rate:.1f}% of duplicate identification. "
                    f"Investigate mapping strategies for duplicates."
                )
            
            # Cleaner mapper
            cleaner_mapper = comparison.get('cleaner_mapper', 'unknown')
            if cleaner_mapper != 'tie' and cleaner_mapper != 'unknown':
                recommendations.append(
                    f"Consider prioritizing {cleaner_mapper.upper()} results - "
                    f"it has lower duplicate rate (cleaner mapping)."
                )
        
        # Success message if excellent
        if correctness_rate >= 90:
            recommendations.append(
                "✓ Excellent validation quality! "
                "High correctness rate indicates strong mapper compliance with taxonomy."
            )
        
        return recommendations
    
    def _format_duplicate_quality(
        self,
        duplicate_reports: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format duplicate quality data for report.
        
        Args:
            duplicate_reports: Raw duplicate comparison data
            
        Returns:
            Formatted duplicate quality section
        """
        map_pro_report = duplicate_reports.get('map_pro_report', {})
        ccq_report = duplicate_reports.get('ccq_report', {})
        comparison = duplicate_reports.get('comparison', {})
        quality_assessment = duplicate_reports.get('quality_assessment', {})
        
        return {
            'map_pro': {
                'duplicate_percentage': map_pro_report.get('duplicate_percentage', 0.0),
                'duplicate_groups': map_pro_report.get('duplicate_groups', 0),
                'has_critical': map_pro_report.get('has_critical', False),
                'has_major': map_pro_report.get('has_major', False)
            },
            'ccq': {
                'duplicate_percentage': ccq_report.get('duplicate_percentage', 0.0),
                'duplicate_groups': ccq_report.get('duplicate_groups', 0),
                'has_critical': ccq_report.get('has_critical', False),
                'has_major': ccq_report.get('has_major', False)
            },
            'comparison': {
                'agreement_rate': comparison.get('agreement_rate', 0.0),
                'duplicates_in_both': comparison.get('duplicates_in_both', 0),
                'duplicates_only_map_pro': comparison.get('duplicates_only_map_pro', 0),
                'duplicates_only_ccq': comparison.get('duplicates_only_ccq', 0),
                'cleaner_mapper': comparison.get('cleaner_mapper', 'unknown')
            },
            'quality_assessment': {
                'overall_status': quality_assessment.get('overall_status', 'UNKNOWN'),
                'flags': quality_assessment.get('flags', []),
                'recommendations': quality_assessment.get('recommendations', []),
                'summary': quality_assessment.get('summary', '')
            }
        }


__all__ = ['ReconciliationReporter']