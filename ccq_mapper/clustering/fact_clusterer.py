"""
Fact Clusterer
==============

Clusters facts into natural groups by property similarity.

CRITICAL: Groups by PROPERTIES, not concept relationships.
"""

from typing import Dict, Any, List
from collections import defaultdict

from core.system_logger import get_logger

logger = get_logger(__name__)


class FactClusterer:
    """
    Cluster facts into natural groups based on property similarity.
    
    Clustering dimensions:
    - Statement type (balance sheet, income, cash flow)
    - Period type (instant, duration)
    - Context (same period, entity, dimensions)
    - Monetary type (currency, shares, pure)
    - Aggregation level (total, subtotal, line item)
    
    Uses multi-pass clustering for hierarchical grouping.
    """
    
    def cluster_facts(
        self,
        classified_facts: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Cluster facts into natural groups.
        
        Args:
            classified_facts: Facts with classification information
            
        Returns:
            Dictionary mapping cluster IDs to fact lists
        """
        logger.info(f"Clustering {len(classified_facts)} facts")
        
        # Pass 1: Group by statement type
        statement_groups = self._group_by_statement(classified_facts)
        
        # Pass 2: Within each statement, group by period
        period_clusters = {}
        for stmt_type, facts in statement_groups.items():
            period_clusters[stmt_type] = self._group_by_period(facts)
        
        # Pass 3: Within periods, group by context
        final_clusters = {}
        cluster_id = 0
        
        for stmt_type, period_groups in period_clusters.items():
            for period_key, facts in period_groups.items():
                context_groups = self._group_by_context(facts)
                
                for ctx_key, ctx_facts in context_groups.items():
                    cluster_key = f"{stmt_type}_{period_key}_{ctx_key}"
                    final_clusters[cluster_key] = ctx_facts
                    cluster_id += 1
        
        logger.info(f"Created {len(final_clusters)} clusters")
        
        return final_clusters
    
    def _group_by_statement(
        self,
        facts: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group facts by predicted statement type."""
        groups = defaultdict(list)
        
        for fact in facts:
            classification = fact.get('classification', {})
            stmt_type = classification.get('predicted_statement', 'other')
            groups[stmt_type].append(fact)
        
        return dict(groups)
    
    def _group_by_period(
        self,
        facts: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group facts by period type and dates."""
        groups = defaultdict(list)
        
        for fact in facts:
            classification = fact.get('classification', {})
            temporal_type = classification.get('temporal_type', 'unknown')
            
            # Get period dates for key
            extracted_props = fact.get('extracted_properties', {})
            context_info = extracted_props.get('context_info', {})
            period_info = context_info.get('period', {})
            
            if temporal_type == 'instant':
                instant = period_info.get('instant')
                period_key = f"instant_{instant}"
            elif temporal_type == 'duration':
                start = period_info.get('start')
                end = period_info.get('end')
                period_key = f"duration_{start}_{end}"
            else:
                period_key = 'unknown'
            
            groups[period_key].append(fact)
        
        return dict(groups)
    
    def _group_by_context(
        self,
        facts: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group facts by context (entity, dimensions)."""
        groups = defaultdict(list)
        
        for fact in facts:
            extracted_props = fact.get('extracted_properties', {})
            context_info = extracted_props.get('context_info', {})
            
            # Build context key
            entity = context_info.get('entity', {})
            entity_value = entity.get('value', 'unknown')
            
            has_dimensions = context_info.get('has_segments') or context_info.get('has_scenarios')
            
            if has_dimensions:
                # Create key including dimension info
                dimensions = context_info.get('dimensions', [])
                dim_key = '_'.join(f"{d.get('dimension')}={d.get('member', d.get('value'))}" 
                                   for d in dimensions)
                context_key = f"{entity_value}_{dim_key}"
            else:
                context_key = f"{entity_value}_default"
            
            groups[context_key].append(fact)
        
        return dict(groups)
    
    def analyze_cluster(
        self,
        cluster_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze properties of a cluster.
        
        Returns summary statistics and common properties.
        """
        if not cluster_facts:
            return {
                'size': 0,
                'properties': {}
            }
        
        # Count classification types
        statement_types = defaultdict(int)
        temporal_types = defaultdict(int)
        monetary_types = defaultdict(int)
        aggregation_levels = defaultdict(int)
        
        for fact in cluster_facts:
            classification = fact.get('classification', {})
            statement_types[classification.get('predicted_statement')] += 1
            temporal_types[classification.get('temporal_type')] += 1
            monetary_types[classification.get('monetary_type')] += 1
            aggregation_levels[classification.get('aggregation_level')] += 1
        
        # Find most common (consensus) values
        return {
            'size': len(cluster_facts),
            'properties': {
                'statement_type': max(statement_types, key=statement_types.get) if statement_types else 'unknown',
                'temporal_type': max(temporal_types, key=temporal_types.get) if temporal_types else 'unknown',
                'monetary_type': max(monetary_types, key=monetary_types.get) if monetary_types else 'unknown',
                'aggregation_level': max(aggregation_levels, key=aggregation_levels.get) if aggregation_levels else 'unknown'
            },
            'diversity': {
                'statement_types': len(statement_types),
                'temporal_types': len(temporal_types),
                'monetary_types': len(monetary_types),
                'aggregation_levels': len(aggregation_levels)
            }
        }
    
    def merge_clusters(
        self,
        cluster1: List[Dict[str, Any]],
        cluster2: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge two clusters if they are similar enough.
        
        Returns merged cluster or None if not mergeable.
        """
        analysis1 = self.analyze_cluster(cluster1)
        analysis2 = self.analyze_cluster(cluster2)
        
        # Check if properties match
        props1 = analysis1['properties']
        props2 = analysis2['properties']
        
        matches = sum(1 for k in props1 if props1.get(k) == props2.get(k))
        
        # Require 3 out of 4 properties to match
        if matches >= 3:
            return cluster1 + cluster2
        
        return None
    
    def split_cluster(
        self,
        cluster_facts: List[Dict[str, Any]],
        split_by: str = 'aggregation_level'
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Split a cluster by a specific property.
        
        Useful for separating totals from line items.
        """
        subclusters = defaultdict(list)
        
        for fact in cluster_facts:
            classification = fact.get('classification', {})
            split_value = classification.get(split_by, 'unknown')
            subclusters[split_value].append(fact)
        
        return dict(subclusters)
    
    def get_cluster_hierarchy(
        self,
        cluster_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Determine hierarchical structure within a cluster.
        
        Groups facts by aggregation level to build statement hierarchy.
        """
        # Split by aggregation level
        levels = self.split_cluster(cluster_facts, 'aggregation_level')
        
        # Order by aggregation score
        ordered_levels = {}
        level_order = ['total', 'subtotal', 'line_item', 'abstract']
        
        for level in level_order:
            if level in levels:
                ordered_levels[level] = levels[level]
        
        return {
            'levels': ordered_levels,
            'total_count': sum(len(facts) for facts in ordered_levels.values()),
            'level_counts': {k: len(v) for k, v in ordered_levels.items()}
        }


__all__ = ['FactClusterer']