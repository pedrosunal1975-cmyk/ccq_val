"""
Error Report Generator
======================

Location: ccq_val/engines/ccq_mapper/adapters/error_reporter.py

Generates comprehensive error analysis reports.

Classes:
- ErrorReporter: Creates and saves error analysis reports
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import Counter

from .error_models import ErrorSummary


class ErrorReporter:
    """Generates comprehensive error analysis reports."""
    
    def generate_report(
        self,
        summaries: List[ErrorSummary],
        output_path: Path
    ):
        """
        Generate comprehensive error report.
        
        Args:
            summaries: List of ErrorSummary objects
            output_path: Path to save report JSON file
        """
        report = {
            'analysis_date': str(Path.cwd()),
            'summaries': [],
            'overall_statistics': self._calculate_overall_stats(summaries),
            'recommendations': self._generate_recommendations(summaries)
        }
        
        # Add summaries (convert to dicts)
        for summary in summaries:
            report['summaries'].append(summary.to_dict())
        
        # Save report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n{'='*80}")
        print(f"Report saved to: {output_path}")
        print(f"{'='*80}")
    
    def _calculate_overall_stats(
        self,
        summaries: List[ErrorSummary]
    ) -> Dict:
        """
        Calculate overall statistics across all summaries.
        
        Args:
            summaries: List of ErrorSummary objects
            
        Returns:
            Dictionary of overall statistics
        """
        total_facts = sum(s.total_facts for s in summaries)
        total_failed = sum(s.failed_facts for s in summaries)
        
        all_categories = Counter()
        all_missing_fields = Counter()
        
        for summary in summaries:
            all_categories.update(summary.error_categories)
            all_missing_fields.update(summary.missing_fields_freq)
        
        return {
            'total_facts_processed': total_facts,
            'total_failures': total_failed,
            'overall_error_rate': (
                total_failed / total_facts * 100 
                if total_facts > 0 else 0
            ),
            'error_categories': dict(all_categories),
            'missing_fields': dict(all_missing_fields)
        }
    
    def _generate_recommendations(
        self,
        summaries: List[ErrorSummary]
    ) -> List[str]:
        """
        Generate actionable recommendations based on error patterns.
        
        Args:
            summaries: List of ErrorSummary objects
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check for high error rates
        high_error_statements = [
            s for s in summaries if s.error_rate > 20
        ]
        
        if high_error_statements:
            recommendations.append(
                f"HIGH PRIORITY: {len(high_error_statements)} statements "
                f"have >20% error rate"
            )
        
        # Check for missing concept identifiers
        all_missing = Counter()
        for summary in summaries:
            all_missing.update(summary.missing_fields_freq)
        
        if 'concept' in all_missing or 'qname' in all_missing:
            recommendations.append(
                "CRITICAL: Missing concept identifiers - "
                "check source data structure"
            )
        
        # Check for unexpected CCQ errors
        ccq_errors = [
            s for s in summaries 
            if s.adapter_type == 'ccq' and s.failed_facts > 0
        ]
        if ccq_errors:
            recommendations.append(
                f"UNEXPECTED: CCQ adapter has errors in "
                f"{len(ccq_errors)} statements (should be 0)"
            )
        
        # Check for Map Pro high failure rates
        map_pro_high = [
            s for s in summaries 
            if s.adapter_type == 'map_pro' and s.error_rate > 50
        ]
        if map_pro_high:
            recommendations.append(
                f"CRITICAL: Map Pro has >50% error rate in "
                f"{len(map_pro_high)} statements"
            )
        
        return recommendations
    
    def print_summary(self, summaries: List[ErrorSummary]):
        """
        Print summary statistics to console.
        
        Args:
            summaries: List of ErrorSummary objects
        """
        overall = self._calculate_overall_stats(summaries)
        recommendations = self._generate_recommendations(summaries)
        
        print(f"\n{'='*80}")
        print("OVERALL STATISTICS")
        print(f"{'='*80}")
        print(f"Total facts processed: {overall['total_facts_processed']}")
        print(f"Total failures: {overall['total_failures']}")
        print(f"Overall error rate: {overall['overall_error_rate']:.1f}%")
        
        print(f"\n{'='*80}")
        print("RECOMMENDATIONS")
        print(f"{'='*80}")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("✅ No critical issues found")