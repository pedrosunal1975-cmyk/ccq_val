# File: engines/ccq_mapper/analysis/duplicate_summary_aggregator.py

"""
Duplicate Summary Aggregator
=============================

Aggregates duplicate analysis results into summary reports.

Responsibility:
- Summarize duplicates by statement type
- Summarize duplicates by value type
- Summarize duplicates by significance level
- Calculate percentages and breakdowns
"""

from typing import Dict, Any, List
from collections import defaultdict


class DuplicateSummaryAggregator:
    """Aggregates duplicate analysis into summaries."""
    
    @staticmethod
    def summarize_by_statement(
        enriched_duplicates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Summarize duplicates by statement type.
        
        Args:
            enriched_duplicates: List of enriched duplicate profiles
            
        Returns:
            Summary dictionary with breakdown by statement type:
            - count: Number of duplicate groups
            - facts: Total duplicate facts
            - monetary_breakdown: Breakdown by monetary type
            - material_variance_count: Count with >1% variance
            - source_breakdown: Breakdown by source
            - percentage: Percentage of total facts
        """
        summary = defaultdict(lambda: {
            'count': 0,
            'facts': 0,
            'monetary_breakdown': defaultdict(int),
            'material_variance_count': 0,
            'source_breakdown': defaultdict(int)
        })
        
        total_facts = sum(dup['duplicate_count'] for dup in enriched_duplicates)
        
        for dup in enriched_duplicates:
            stmt_type = dup['classification']['statement_type']
            money_type = dup['classification']['monetary_type']
            source = dup['source']
            
            summary[stmt_type]['count'] += 1
            summary[stmt_type]['facts'] += dup['duplicate_count']
            summary[stmt_type]['monetary_breakdown'][money_type] += 1
            summary[stmt_type]['source_breakdown'][source] += 1
            
            # Count material variance (>1%)
            if dup['variance_percentage'] > 1.0:
                summary[stmt_type]['material_variance_count'] += 1
        
        # Calculate percentages
        for stmt_type, data in summary.items():
            data['percentage'] = round(
                (data['facts'] / total_facts) * 100, 1
            ) if total_facts > 0 else 0.0
        
        return dict(summary)
    
    @staticmethod
    def summarize_by_value_type(
        enriched_duplicates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Summarize duplicates by value/monetary type.
        
        Args:
            enriched_duplicates: List of enriched duplicate profiles
            
        Returns:
            Summary dictionary with breakdown by value type:
            - count: Number of duplicate groups
            - facts: Total duplicate facts
            - statement_breakdown: Breakdown by statement type
            - percentage: Percentage of total facts
        """
        summary = defaultdict(lambda: {
            'count': 0,
            'facts': 0,
            'statement_breakdown': defaultdict(int)
        })
        
        total_facts = sum(dup['duplicate_count'] for dup in enriched_duplicates)
        
        for dup in enriched_duplicates:
            money_type = dup['classification']['monetary_type']
            stmt_type = dup['classification']['statement_type']
            
            summary[money_type]['count'] += 1
            summary[money_type]['facts'] += dup['duplicate_count']
            summary[money_type]['statement_breakdown'][stmt_type] += 1
        
        # Calculate percentages
        for money_type, data in summary.items():
            data['percentage'] = round(
                (data['facts'] / total_facts) * 100, 1
            ) if total_facts > 0 else 0.0
        
        return dict(summary)
    
    @staticmethod
    def summarize_by_significance(
        enriched_duplicates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Summarize duplicates by financial significance.
        
        Args:
            enriched_duplicates: List of enriched duplicate profiles
            
        Returns:
            Summary dictionary with breakdown by significance level:
            - count: Number of duplicate groups
            - facts: Total duplicate facts
            - examples: Example duplicates (max 5 per level)
            - percentage: Percentage of total facts
        """
        summary = defaultdict(lambda: {
            'count': 0,
            'facts': 0,
            'examples': []
        })
        
        total_facts = sum(dup['duplicate_count'] for dup in enriched_duplicates)
        
        for dup in enriched_duplicates:
            sig_level = dup['significance']['level']
            
            summary[sig_level]['count'] += 1
            summary[sig_level]['facts'] += dup['duplicate_count']
            
            # Store examples (max 5 per level)
            if len(summary[sig_level]['examples']) < 5:
                summary[sig_level]['examples'].append({
                    'concept': dup['concept'],
                    'statement': dup['classification']['statement_type'],
                    'variance_pct': dup['variance_percentage']
                })
        
        # Calculate percentages
        for sig_level, data in summary.items():
            data['percentage'] = round(
                (data['facts'] / total_facts) * 100, 1
            ) if total_facts > 0 else 0.0
        
        return dict(summary)


__all__ = ['DuplicateSummaryAggregator']