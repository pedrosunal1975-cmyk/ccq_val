# File: engines/ccq_mapper/analysis/clustering_scorer.py

"""
Clustering Scorer
=================

Calculates clustering effectiveness metrics.

Responsibility:
- Calculate clustering rates
- Analyze cluster distribution
- Compute cluster quality metrics
"""

from typing import Dict, Any, List


class ClusteringScorer:
    """Scores clustering effectiveness."""
    
    @staticmethod
    def calculate_clustering_success(
        clusters: Dict[str, List[Dict[str, Any]]],
        total_facts: int
    ) -> Dict[str, Any]:
        """
        Calculate clustering success metrics.
        
        Args:
            clusters: Clustered facts dictionary
            total_facts: Total number of facts
            
        Returns:
            Clustering success dictionary with:
            - cluster_count: Number of clusters
            - clustered_facts: Number of facts in clusters
            - clustering_rate: Percentage of facts clustered
            - average_cluster_size: Mean facts per cluster
        """
        cluster_count = len(clusters)
        clustered_facts = sum(len(facts) for facts in clusters.values())
        
        clustering_rate = (
            clustered_facts / total_facts * 100
            if total_facts > 0 else 0.0
        )
        
        # Calculate average cluster size
        avg_cluster_size = (
            clustered_facts / cluster_count
            if cluster_count > 0 else 0.0
        )
        
        return {
            'cluster_count': cluster_count,
            'clustered_facts': clustered_facts,
            'clustering_rate': round(clustering_rate, 2),
            'average_cluster_size': round(avg_cluster_size, 2)
        }


__all__ = ['ClusteringScorer']