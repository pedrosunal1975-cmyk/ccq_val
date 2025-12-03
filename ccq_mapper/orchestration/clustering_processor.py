# File: engines/ccq_mapper/orchestration/clustering_processor.py

"""
Clustering Processor
====================

Handles fact clustering and boundary detection.

Responsibility:
- Cluster facts into natural groups
- Detect statement boundaries
- Organize clusters for construction
"""

from typing import Dict, Any, List

from core.system_logger import get_logger
from ..clustering.fact_clusterer import FactClusterer
from ..clustering.boundary_detector import BoundaryDetector

logger = get_logger(__name__)


class ClusteringProcessor:
    """Processes fact clustering and boundary detection."""
    
    def __init__(self):
        """Initialize clustering processor."""
        self.fact_clusterer = FactClusterer()
        self.boundary_detector = BoundaryDetector()
        self.logger = logger
    
    def cluster_facts(
        self,
        classified_facts: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Cluster facts into natural groups by similarity.
        
        Args:
            classified_facts: Facts with classifications
            
        Returns:
            Dictionary of statement clusters
        """
        self.logger.info("Clustering facts into groups...")
        
        # Cluster by classification similarity
        clusters = self.fact_clusterer.cluster_facts(classified_facts)
        
        # Detect statement boundaries
        statement_clusters = self.boundary_detector.detect_boundaries(clusters)
        
        return statement_clusters


__all__ = ['ClusteringProcessor']