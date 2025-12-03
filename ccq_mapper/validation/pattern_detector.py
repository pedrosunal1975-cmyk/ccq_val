# File: engines/ccq_mapper/validation/pattern_detector.py

"""
CCQ Null Pattern Detector
==========================

Detects patterns in null value distribution.
This is CCQ-specific - Map Pro doesn't do pattern analysis.

Patterns detected:
- Statement clustering (many nulls in one statement)
- Namespace clustering (nulls concentrated in specific namespaces)
- Confidence correlation (nulls correlate with low classification confidence)
- Temporal patterns (nulls in specific period types)
"""

from typing import Dict, Any, List
from collections import defaultdict

from core.system_logger import get_logger
from .null_quality_constants import (
    PATTERN_CLUSTER_THRESHOLD,
    PATTERN_NAMESPACE_THRESHOLD,
    PATTERN_CONFIDENCE_THRESHOLD,
    NULLABLE_NAMESPACES
)

logger = get_logger(__name__)


class PatternDetector:
    """
    Detects patterns in null value distribution.
    
    CCQ's Unique Capability:
    - Analyzes null clustering by statement, namespace, confidence
    - Identifies systematic issues vs random nulls
    - Provides insights for classification improvement
    """
    
    def __init__(self):
        """Initialize pattern detector."""
        self.patterns_found = []
    
    def detect_patterns(
        self,
        null_analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect patterns across all null analyses.
        
        Args:
            null_analyses: List of null analysis dictionaries
            
        Returns:
            List of detected patterns
        """
        if not null_analyses:
            return []
        
        self.patterns_found = []
        
        # Detect various pattern types
        self._detect_statement_clustering(null_analyses)
        self._detect_namespace_clustering(null_analyses)
        self._detect_confidence_correlation(null_analyses)
        self._detect_temporal_patterns(null_analyses)
        
        return self.patterns_found
    
    def _detect_statement_clustering(
        self,
        null_analyses: List[Dict[str, Any]]
    ) -> None:
        """Detect if nulls cluster in specific statements."""
        statement_counts = defaultdict(int)
        
        for analysis in null_analyses:
            stmt = analysis.get('classification_context', {}).get('statement')
            if stmt:
                statement_counts[stmt] += 1
        
        # Check for clusters
        for statement, count in statement_counts.items():
            if count >= PATTERN_CLUSTER_THRESHOLD:
                self.patterns_found.append({
                    'pattern_type': 'statement_clustering',
                    'statement': statement,
                    'null_count': count,
                    'severity': self._assess_cluster_severity(count),
                    'description': f"{count} nulls concentrated in {statement}",
                    'recommendation': f"Review {statement} classification logic"
                })
    
    def _detect_namespace_clustering(
        self,
        null_analyses: List[Dict[str, Any]]
    ) -> None:
        """Detect if nulls cluster in specific namespaces."""
        namespace_counts = defaultdict(int)
        total_nulls = len(null_analyses)
        
        for analysis in null_analyses:
            qname = analysis.get('qname', '')
            if ':' in qname:
                namespace = qname.split(':')[0]
                namespace_counts[namespace] += 1
        
        # Check for significant clustering
        for namespace, count in namespace_counts.items():
            percentage = (count / total_nulls * 100) if total_nulls > 0 else 0
            
            if percentage > PATTERN_NAMESPACE_THRESHOLD:
                # Check if this namespace is expected to have nulls
                is_expected = namespace in NULLABLE_NAMESPACES
                
                self.patterns_found.append({
                    'pattern_type': 'namespace_clustering',
                    'namespace': namespace,
                    'null_count': count,
                    'percentage': round(percentage, 1),
                    'is_expected': is_expected,
                    'severity': 'low' if is_expected else 'medium',
                    'description': f"{percentage:.1f}% of nulls in {namespace} namespace",
                    'recommendation': (
                        "Expected for this namespace" if is_expected
                        else f"Review {namespace} concept classifications"
                    )
                })
    
    def _detect_confidence_correlation(
        self,
        null_analyses: List[Dict[str, Any]]
    ) -> None:
        """Detect if nulls correlate with low classification confidence."""
        low_confidence_nulls = []
        
        for analysis in null_analyses:
            confidence = analysis.get('classification_context', {}).get('confidence', 1.0)
            
            if confidence < PATTERN_CONFIDENCE_THRESHOLD:
                low_confidence_nulls.append({
                    'qname': analysis.get('qname'),
                    'confidence': confidence
                })
        
        if len(low_confidence_nulls) >= PATTERN_CLUSTER_THRESHOLD:
            avg_confidence = sum(n['confidence'] for n in low_confidence_nulls) / len(low_confidence_nulls)
            
            self.patterns_found.append({
                'pattern_type': 'confidence_correlation',
                'null_count': len(low_confidence_nulls),
                'average_confidence': round(avg_confidence, 3),
                'severity': 'high',
                'description': f"{len(low_confidence_nulls)} nulls with low classification confidence",
                'recommendation': "Uncertain classifications may indicate missing data or classification errors"
            })
    
    def _detect_temporal_patterns(
        self,
        null_analyses: List[Dict[str, Any]]
    ) -> None:
        """Detect if nulls occur in specific temporal types."""
        temporal_counts = defaultdict(int)
        
        for analysis in null_analyses:
            temporal = analysis.get('classification_context', {}).get('temporal_type')
            if temporal:
                temporal_counts[temporal] += 1
        
        # Check for unusual temporal clustering
        for temporal_type, count in temporal_counts.items():
            if count >= PATTERN_CLUSTER_THRESHOLD:
                # Instant nulls in balance sheet are more suspicious
                severity = 'high' if temporal_type == 'instant' else 'medium'
                
                self.patterns_found.append({
                    'pattern_type': 'temporal_clustering',
                    'temporal_type': temporal_type,
                    'null_count': count,
                    'severity': severity,
                    'description': f"{count} nulls with {temporal_type} temporal type",
                    'recommendation': f"Review {temporal_type} facts for missing values"
                })
    
    def _assess_cluster_severity(self, count: int) -> str:
        """Assess severity of clustering."""
        if count >= 20:
            return 'high'
        elif count >= 10:
            return 'medium'
        else:
            return 'low'
    
    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of detected patterns."""
        if not self.patterns_found:
            return {
                'total_patterns': 0,
                'message': 'No significant patterns detected'
            }
        
        severity_counts = defaultdict(int)
        type_counts = defaultdict(int)
        
        for pattern in self.patterns_found:
            severity_counts[pattern['severity']] += 1
            type_counts[pattern['pattern_type']] += 1
        
        return {
            'total_patterns': len(self.patterns_found),
            'by_severity': dict(severity_counts),
            'by_type': dict(type_counts),
            'requires_attention': severity_counts.get('high', 0) > 0
        }


__all__ = ['PatternDetector']