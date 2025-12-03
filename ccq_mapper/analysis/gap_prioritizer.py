# File: engines/ccq_mapper/analysis/gap_prioritizer.py

"""
CCQ Gap Prioritizer
==================

Prioritizes classification gaps by financial importance and impact.

Organizes gaps into priority levels:
- P0 (CRITICAL): Core financial statement line items
- P1 (HIGH): Monetary facts with financial significance
- P2 (MEDIUM): Secondary metrics and dimensional data
- P3 (LOW): Text disclosures and supplementary data

Architecture: Market-agnostic prioritization logic.
"""

from typing import Dict, Any, List
from collections import defaultdict
from core.system_logger import get_logger

logger = get_logger(__name__)


class GapPrioritizer:
    """
    Prioritizes classification gaps by importance.
    
    Responsibilities:
    - Organize gaps by priority level
    - Generate summary by priority
    - Identify critical gaps requiring immediate attention
    - Generate actionable recommendations
    
    Does NOT:
    - Modify gap data
    - Make classification decisions
    - Fix gaps
    """
    
    def __init__(self):
        """Initialize gap prioritizer."""
        self.logger = logger
        self.logger.info("Gap prioritizer initialized")
    
    def prioritize_gaps(
        self,
        enriched_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Organize gaps by priority level.
        
        Args:
            enriched_gaps: List of enriched gap profiles
            
        Returns:
            Prioritized gap analysis
        """
        if not enriched_gaps:
            return self._build_empty_prioritization()
        
        # Organize by priority
        priority_groups = self._group_by_priority(enriched_gaps)
        
        # Generate summaries
        summary_by_priority = self._summarize_by_priority(priority_groups)
        summary_by_significance = self._summarize_by_significance(
            enriched_gaps
        )
        
        # Identify critical gaps
        critical_gaps = priority_groups.get('P0', [])
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            priority_groups,
            enriched_gaps
        )
        
        return {
            'priority_groups': priority_groups,
            'summary_by_priority': summary_by_priority,
            'summary_by_significance': summary_by_significance,
            'critical_gaps': critical_gaps,
            'critical_count': len(critical_gaps),
            'recommendations': recommendations
        }
    
    def _group_by_priority(
        self,
        enriched_gaps: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group gaps by priority level.
        
        Args:
            enriched_gaps: List of enriched gap profiles
            
        Returns:
            Dictionary mapping priority to gap lists
        """
        groups = defaultdict(list)
        
        for gap in enriched_gaps:
            priority = gap.get('priority', 'P3')
            groups[priority].append(gap)
        
        return dict(groups)
    
    def _summarize_by_priority(
        self,
        priority_groups: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics by priority.
        
        Args:
            priority_groups: Groups of gaps by priority
            
        Returns:
            Priority summary dictionary
        """
        summary = {}
        
        total_gaps = sum(len(gaps) for gaps in priority_groups.values())
        
        for priority in ['P0', 'P1', 'P2', 'P3']:
            gaps = priority_groups.get(priority, [])
            count = len(gaps)
            
            # Extract examples
            examples = []
            for gap in gaps[:5]:
                examples.append({
                    'concept': gap.get('concept'),
                    'best_guess_statement': gap.get('best_guess_statement'),
                    'gap_type': gap.get('gap_type')
                })
            
            summary[priority] = {
                'count': count,
                'percentage': round((count / total_gaps) * 100, 1) if total_gaps > 0 else 0.0,
                'examples': examples,
                'description': self._get_priority_description(priority)
            }
        
        return summary
    
    def _summarize_by_significance(
        self,
        enriched_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate summary by significance level.
        
        Args:
            enriched_gaps: List of enriched gap profiles
            
        Returns:
            Significance summary dictionary
        """
        significance_counts = defaultdict(int)
        significance_examples = defaultdict(list)
        
        for gap in enriched_gaps:
            sig = gap.get('significance', {})
            level = sig.get('level', 'LOW')
            significance_counts[level] += 1
            
            if len(significance_examples[level]) < 5:
                significance_examples[level].append({
                    'concept': gap.get('concept'),
                    'reason': sig.get('reason')
                })
        
        total = len(enriched_gaps)
        
        summary = {}
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = significance_counts.get(level, 0)
            summary[level] = {
                'count': count,
                'percentage': round((count / total) * 100, 1) if total > 0 else 0.0,
                'examples': significance_examples.get(level, [])
            }
        
        return summary
    
    def _generate_recommendations(
        self,
        priority_groups: Dict[str, List[Dict[str, Any]]],
        all_gaps: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate actionable recommendations.
        
        Args:
            priority_groups: Groups of gaps by priority
            all_gaps: All enriched gaps
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Critical gaps
        p0_count = len(priority_groups.get('P0', []))
        if p0_count > 0:
            recommendations.append(
                f"URGENT: {p0_count} core financial concepts unclassified - "
                f"review classifier logic immediately"
            )
        
        # High priority gaps
        p1_count = len(priority_groups.get('P1', []))
        if p1_count > 0:
            recommendations.append(
                f"HIGH: {p1_count} financial statement facts unclassified - "
                f"investigate property extraction"
            )
        
        # Check for systematic issues
        gap_type_counts = defaultdict(int)
        for gap in all_gaps:
            gap_type_counts[gap.get('gap_type')] += 1
        
        dominant_gap_type = max(
            gap_type_counts.items(),
            key=lambda x: x[1]
        ) if gap_type_counts else None
        
        if dominant_gap_type:
            gap_type, count = dominant_gap_type
            percentage = (count / len(all_gaps)) * 100
            
            if percentage > 70:
                recommendations.append(
                    f"{int(percentage)}% of gaps are '{gap_type}' - "
                    f"systematic issue detected"
                )
        
        # Missing properties
        missing_props = defaultdict(int)
        for gap in all_gaps:
            for missing in gap.get('missing_classifications', []):
                missing_props[missing] += 1
        
        if missing_props:
            most_missing = max(missing_props.items(), key=lambda x: x[1])
            prop_name, prop_count = most_missing
            prop_pct = (prop_count / len(all_gaps)) * 100
            
            if prop_pct > 50:
                recommendations.append(
                    f"{int(prop_pct)}% gaps missing {prop_name} - "
                    f"review property extractor"
                )
        
        # Best guess statements
        statement_counts = defaultdict(int)
        for gap in all_gaps:
            statement_counts[gap.get('best_guess_statement')] += 1
        
        if statement_counts.get('other', 0) / len(all_gaps) > 0.7:
            recommendations.append(
                "Most gaps are supplementary data ('other') - "
                "this is expected behavior"
            )
        
        # If no specific recommendations, provide general guidance
        if not recommendations:
            recommendations.append(
                "Review individual gap characterizations for specific issues"
            )
        
        return recommendations
    
    def _get_priority_description(self, priority: str) -> str:
        """
        Get human-readable description of priority level.
        
        Args:
            priority: Priority level (P0, P1, P2, P3)
            
        Returns:
            Description string
        """
        descriptions = {
            'P0': 'CRITICAL - Core financial statement line items',
            'P1': 'HIGH - Financial statement numeric facts',
            'P2': 'MEDIUM - Secondary metrics and dimensional data',
            'P3': 'LOW - Text disclosures and supplementary data'
        }
        return descriptions.get(priority, 'Unknown priority')
    
    def _build_empty_prioritization(self) -> Dict[str, Any]:
        """Build empty prioritization result."""
        return {
            'priority_groups': {},
            'summary_by_priority': {
                'P0': {'count': 0, 'percentage': 0.0, 'examples': []},
                'P1': {'count': 0, 'percentage': 0.0, 'examples': []},
                'P2': {'count': 0, 'percentage': 0.0, 'examples': []},
                'P3': {'count': 0, 'percentage': 0.0, 'examples': []}
            },
            'summary_by_significance': {
                'CRITICAL': {'count': 0, 'percentage': 0.0, 'examples': []},
                'HIGH': {'count': 0, 'percentage': 0.0, 'examples': []},
                'MEDIUM': {'count': 0, 'percentage': 0.0, 'examples': []},
                'LOW': {'count': 0, 'percentage': 0.0, 'examples': []}
            },
            'critical_gaps': [],
            'critical_count': 0,
            'recommendations': ['No classification gaps detected']
        }


__all__ = ['GapPrioritizer']