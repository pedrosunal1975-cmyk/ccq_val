"""
Boundary Detector
=================

Detects natural boundaries between statements within clusters.

CRITICAL: Detects by PROPERTY DISCONTINUITIES, not concept relationships.
"""

from typing import Dict, Any, List, Tuple
from collections import defaultdict

from core.system_logger import get_logger

logger = get_logger(__name__)


class BoundaryDetector:
    """
    Detect natural boundaries between statements within fact clusters.
    
    Boundaries detected by:
    - Sudden changes in aggregation level (totals mark boundaries)
    - Context changes (period switches)
    - Abstract facts (section headers)
    - Property discontinuities
    """
    
    def detect_boundaries(
        self,
        clusters: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect and refine statement boundaries within clusters.
        
        Args:
            clusters: Initial clusters from FactClusterer
            
        Returns:
            Refined clusters with statement boundaries
        """
        logger.info(f"Detecting boundaries in {len(clusters)} clusters")
        
        refined_clusters = {}
        
        for cluster_id, facts in clusters.items():
            # Check if cluster needs splitting
            sub_clusters = self._split_by_boundaries(facts)
            
            if len(sub_clusters) > 1:
                # Multiple statements found in cluster
                for i, sub_facts in enumerate(sub_clusters):
                    refined_id = f"{cluster_id}_part{i+1}"
                    refined_clusters[refined_id] = sub_facts
            else:
                # Single coherent statement
                refined_clusters[cluster_id] = facts
        
        logger.info(f"Refined to {len(refined_clusters)} clusters")
        
        return refined_clusters
    
    def _split_by_boundaries(
        self,
        facts: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Split a cluster at detected boundaries.
        
        Returns list of sub-clusters.
        """
        if len(facts) <= 1:
            return [facts]
        
        # Detect boundary points
        boundaries = self._find_boundary_points(facts)
        
        if not boundaries:
            return [facts]
        
        # Split at boundaries
        sub_clusters = []
        start = 0
        
        for boundary_idx in boundaries:
            if boundary_idx > start:
                sub_clusters.append(facts[start:boundary_idx])
            start = boundary_idx
        
        # Add final segment
        if start < len(facts):
            sub_clusters.append(facts[start:])
        
        return [sc for sc in sub_clusters if sc]  # Filter empty
    
    def _find_boundary_points(
        self,
        facts: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Find indices where boundaries should be placed.
        
        Boundaries indicated by:
        1. Total facts (aggregation level changes)
        2. Abstract facts (section headers)
        3. Period changes
        4. Large gaps in fact ordering
        """
        boundaries = []
        
        for i in range(1, len(facts)):
            if self._is_boundary(facts[i-1], facts[i]):
                boundaries.append(i)
        
        return boundaries
    
    def _is_boundary(
        self,
        fact1: Dict[str, Any],
        fact2: Dict[str, Any]
    ) -> bool:
        """
        Check if there's a boundary between two consecutive facts.
        """
        # Extract classifications
        class1 = fact1.get('classification', {})
        class2 = fact2.get('classification', {})
        
        # Boundary 1: Aggregation level jump (total after line items)
        agg1 = class1.get('aggregation_level', '')
        agg2 = class2.get('aggregation_level', '')
        
        if agg1 in ['line_item', 'subtotal'] and agg2 == 'total':
            return True
        
        # Boundary 2: Abstract fact (section header)
        if agg2 == 'abstract':
            return True
        
        # Boundary 3: Statement type change
        stmt1 = class1.get('predicted_statement', '')
        stmt2 = class2.get('predicted_statement', '')
        
        if stmt1 != stmt2 and stmt1 and stmt2:
            return True
        
        # Boundary 4: Period change
        if self._has_period_change(fact1, fact2):
            return True
        
        return False
    
    def _has_period_change(
        self,
        fact1: Dict[str, Any],
        fact2: Dict[str, Any]
    ) -> bool:
        """Check if period changed between two facts."""
        props1 = fact1.get('extracted_properties', {})
        props2 = fact2.get('extracted_properties', {})
        
        ctx1 = props1.get('context_info', {})
        ctx2 = props2.get('context_info', {})
        
        period1 = ctx1.get('period', {})
        period2 = ctx2.get('period', {})
        
        # Compare periods
        if period1.get('type') != period2.get('type'):
            return True
        
        if period1.get('instant') != period2.get('instant'):
            return True
        
        if period1.get('end') != period2.get('end'):
            return True
        
        return False
    
    def group_by_statement_type(
        self,
        clusters: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Group refined clusters by statement type.
        
        Returns:
            Nested dict: {statement_type: {cluster_id: [facts]}}
        """
        grouped = defaultdict(dict)
        
        for cluster_id, facts in clusters.items():
            if not facts:
                continue
            
            # Determine statement type from majority vote
            stmt_votes = defaultdict(int)
            for fact in facts:
                classification = fact.get('classification', {})
                stmt_type = classification.get('predicted_statement', 'other')
                stmt_votes[stmt_type] += 1
            
            # Get most common statement type
            stmt_type = max(stmt_votes, key=stmt_votes.get) if stmt_votes else 'other'
            grouped[stmt_type][cluster_id] = facts
        
        return dict(grouped)
    
    def detect_statement_sections(
        self,
        facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect logical sections within a statement.
        
        Sections are groups of related line items under a common parent.
        """
        sections = []
        current_section = {
            'header': None,
            'facts': []
        }
        
        for fact in facts:
            classification = fact.get('classification', {})
            agg_level = classification.get('aggregation_level', '')
            
            # Abstract fact starts new section
            if agg_level == 'abstract':
                if current_section['facts']:
                    sections.append(current_section)
                current_section = {
                    'header': fact,
                    'facts': []
                }
            # Subtotal ends a section
            elif agg_level == 'subtotal':
                current_section['facts'].append(fact)
                sections.append(current_section)
                current_section = {
                    'header': None,
                    'facts': []
                }
            # Total ends statement
            elif agg_level == 'total':
                if current_section['facts']:
                    sections.append(current_section)
                sections.append({
                    'header': None,
                    'facts': [fact],
                    'is_total': True
                })
                current_section = {
                    'header': None,
                    'facts': []
                }
            # Line item continues section
            else:
                current_section['facts'].append(fact)
        
        # Add final section
        if current_section['facts']:
            sections.append(current_section)
        
        return sections
    
    def validate_boundary(
        self,
        cluster1: List[Dict[str, Any]],
        cluster2: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate that a boundary between two clusters is correct.
        
        Checks for:
        - Property consistency within clusters
        - Property differences between clusters
        """
        if not cluster1 or not cluster2:
            return {
                'valid': False,
                'reason': 'Empty cluster'
            }
        
        # Check internal consistency
        cluster1_consistent = self._check_cluster_consistency(cluster1)
        cluster2_consistent = self._check_cluster_consistency(cluster2)
        
        if not cluster1_consistent or not cluster2_consistent:
            return {
                'valid': False,
                'reason': 'Clusters not internally consistent'
            }
        
        # Check that clusters are different
        different = self._check_cluster_difference(cluster1, cluster2)
        
        if not different:
            return {
                'valid': False,
                'reason': 'Clusters too similar - boundary unnecessary'
            }
        
        return {
            'valid': True,
            'confidence': 0.8
        }
    
    def _check_cluster_consistency(self, cluster: List[Dict[str, Any]]) -> bool:
        """Check if cluster has consistent properties."""
        if len(cluster) <= 1:
            return True
        
        # Check statement type consistency
        stmt_types = set()
        for fact in cluster:
            classification = fact.get('classification', {})
            stmt_types.add(classification.get('predicted_statement'))
        
        # Allow at most 2 different statement types (some overlap is OK)
        return len(stmt_types) <= 2
    
    def _check_cluster_difference(
        self,
        cluster1: List[Dict[str, Any]],
        cluster2: List[Dict[str, Any]]
    ) -> bool:
        """Check if two clusters are sufficiently different."""
        # Get representative facts
        fact1 = cluster1[0]
        fact2 = cluster2[0]
        
        class1 = fact1.get('classification', {})
        class2 = fact2.get('classification', {})
        
        # Check key properties
        differences = 0
        
        if class1.get('predicted_statement') != class2.get('predicted_statement'):
            differences += 1
        
        if class1.get('temporal_type') != class2.get('temporal_type'):
            differences += 1
        
        # Require at least one key difference
        return differences >= 1


__all__ = ['BoundaryDetector']