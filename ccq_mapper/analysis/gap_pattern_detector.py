# File: engines/ccq_mapper/analysis/gap_pattern_detector.py

"""
CCQ Gap Pattern Detector
========================

Detects systematic patterns in classification gaps.

Identifies patterns such as:
- Namespace concentration (all gaps from one taxonomy)
- Property concentration (all missing same property)
- Statement concentration (all should go to one statement)
- Temporal patterns (all instant or all duration)

This helps identify root causes of classification failures.

Architecture: Market-agnostic pattern detection.
"""

from typing import Dict, Any, List
from collections import defaultdict, Counter
from core.system_logger import get_logger

logger = get_logger(__name__)


PATTERN_THRESHOLD = 0.7  # 70% concentration indicates pattern


class GapPatternDetector:
    """
    Detects systematic patterns in classification gaps.
    
    Responsibilities:
    - Analyze gap distribution across dimensions
    - Detect concentration patterns
    - Identify systematic issues
    - Calculate concern levels
    
    Does NOT:
    - Modify gap data
    - Make classification decisions
    - Suggest fixes
    """
    
    def __init__(self):
        """Initialize gap pattern detector."""
        self.logger = logger
        self.logger.info("Gap pattern detector initialized")
    
    def detect_patterns(
        self,
        enriched_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect patterns across all gaps.
        
        Args:
            enriched_gaps: List of enriched gap profiles
            
        Returns:
            Pattern analysis dictionary
        """
        if not enriched_gaps:
            return self._build_empty_patterns()
        
        patterns = {
            'namespace_concentration': self._detect_namespace_pattern(
                enriched_gaps
            ),
            'property_concentration': self._detect_property_pattern(
                enriched_gaps
            ),
            'statement_concentration': self._detect_statement_pattern(
                enriched_gaps
            ),
            'temporal_concentration': self._detect_temporal_pattern(
                enriched_gaps
            ),
            'gap_type_distribution': self._analyze_gap_types(
                enriched_gaps
            )
        }
        
        return patterns
    
    def _detect_namespace_pattern(
        self,
        enriched_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect if gaps concentrate in specific taxonomies.
        
        Args:
            enriched_gaps: List of enriched gap profiles
            
        Returns:
            Namespace pattern analysis
        """
        namespace_counts = Counter()
        
        for gap in enriched_gaps:
            concept = gap.get('concept', '')
            namespace = self._extract_namespace(concept)
            if namespace:
                namespace_counts[namespace] += 1
        
        if not namespace_counts:
            return {
                'detected': False,
                'concern_level': 'NONE'
            }
        
        total = len(enriched_gaps)
        dominant_namespace = namespace_counts.most_common(1)[0]
        dominant_name, dominant_count = dominant_namespace
        dominant_pct = (dominant_count / total) * 100
        
        is_concentrated = dominant_pct > (PATTERN_THRESHOLD * 100)
        
        return {
            'detected': is_concentrated,
            'dominant_namespace': dominant_name,
            'dominant_count': dominant_count,
            'dominant_percentage': round(dominant_pct, 1),
            'distribution': dict(namespace_counts),
            'concern_level': self._assess_concern_level(dominant_pct),
            'interpretation': self._interpret_namespace_pattern(
                dominant_name,
                dominant_pct
            )
        }
    
    def _detect_property_pattern(
        self,
        enriched_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect if gaps share missing properties.
        
        Args:
            enriched_gaps: List of enriched gap profiles
            
        Returns:
            Property pattern analysis
        """
        missing_property_counts = Counter()
        
        for gap in enriched_gaps:
            missing = gap.get('missing_classifications', [])
            for missing_item in missing:
                missing_property_counts[missing_item] += 1
        
        if not missing_property_counts:
            return {
                'detected': False,
                'concern_level': 'NONE'
            }
        
        total = len(enriched_gaps)
        dominant_missing = missing_property_counts.most_common(1)[0]
        missing_name, missing_count = dominant_missing
        missing_pct = (missing_count / total) * 100
        
        is_concentrated = missing_pct > (PATTERN_THRESHOLD * 100)
        
        return {
            'detected': is_concentrated,
            'dominant_missing': missing_name,
            'dominant_count': missing_count,
            'dominant_percentage': round(missing_pct, 1),
            'distribution': dict(missing_property_counts),
            'concern_level': self._assess_concern_level(missing_pct),
            'interpretation': self._interpret_property_pattern(
                missing_name,
                missing_pct
            )
        }
    
    def _detect_statement_pattern(
        self,
        enriched_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect if gaps concentrate in specific statements.
        
        Args:
            enriched_gaps: List of enriched gap profiles
            
        Returns:
            Statement pattern analysis
        """
        statement_counts = Counter()
        
        for gap in enriched_gaps:
            statement = gap.get('best_guess_statement', 'unknown')
            statement_counts[statement] += 1
        
        if not statement_counts:
            return {
                'detected': False,
                'concern_level': 'NONE'
            }
        
        total = len(enriched_gaps)
        dominant_statement = statement_counts.most_common(1)[0]
        stmt_name, stmt_count = dominant_statement
        stmt_pct = (stmt_count / total) * 100
        
        is_concentrated = stmt_pct > (PATTERN_THRESHOLD * 100)
        
        return {
            'detected': is_concentrated,
            'dominant_statement': stmt_name,
            'dominant_count': stmt_count,
            'dominant_percentage': round(stmt_pct, 1),
            'distribution': dict(statement_counts),
            'concern_level': self._assess_statement_concern(
                stmt_name,
                stmt_pct
            ),
            'interpretation': self._interpret_statement_pattern(
                stmt_name,
                stmt_pct
            )
        }
    
    def _detect_temporal_pattern(
        self,
        enriched_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect temporal patterns in gaps.
        
        Args:
            enriched_gaps: List of enriched gap profiles
            
        Returns:
            Temporal pattern analysis
        """
        temporal_counts = Counter()
        
        for gap in enriched_gaps:
            props = gap.get('available_properties', {})
            period_type = props.get('period_type', 'unknown')
            temporal_counts[period_type] += 1
        
        if not temporal_counts:
            return {
                'detected': False,
                'concern_level': 'NONE'
            }
        
        total = len(enriched_gaps)
        
        instant_count = temporal_counts.get('instant', 0)
        duration_count = temporal_counts.get('duration', 0)
        unknown_count = temporal_counts.get('unknown', 0)
        
        instant_pct = (instant_count / total) * 100
        duration_pct = (duration_count / total) * 100
        unknown_pct = (unknown_count / total) * 100
        
        is_concentrated = (
            instant_pct > (PATTERN_THRESHOLD * 100) or
            duration_pct > (PATTERN_THRESHOLD * 100)
        )
        
        return {
            'detected': is_concentrated,
            'instant_count': instant_count,
            'duration_count': duration_count,
            'unknown_count': unknown_count,
            'instant_percentage': round(instant_pct, 1),
            'duration_percentage': round(duration_pct, 1),
            'unknown_percentage': round(unknown_pct, 1),
            'concern_level': self._assess_temporal_concern(unknown_pct),
            'interpretation': self._interpret_temporal_pattern(
                instant_pct,
                duration_pct,
                unknown_pct
            )
        }
    
    def _analyze_gap_types(
        self,
        enriched_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze distribution of gap types.
        
        Args:
            enriched_gaps: List of enriched gap profiles
            
        Returns:
            Gap type distribution
        """
        gap_type_counts = Counter()
        
        for gap in enriched_gaps:
            gap_type = gap.get('gap_type', 'unknown')
            gap_type_counts[gap_type] += 1
        
        total = len(enriched_gaps)
        
        distribution = {}
        for gap_type, count in gap_type_counts.items():
            distribution[gap_type] = {
                'count': count,
                'percentage': round((count / total) * 100, 1)
            }
        
        return distribution
    
    def _extract_namespace(self, concept: str) -> str:
        """Extract namespace from concept."""
        if ':' in concept:
            return concept.split(':')[0]
        return 'unknown'
    
    def _assess_concern_level(self, percentage: float) -> str:
        """
        Assess concern level based on concentration percentage.
        
        Args:
            percentage: Concentration percentage
            
        Returns:
            Concern level string
        """
        if percentage >= 90:
            return 'HIGH'
        elif percentage >= 70:
            return 'MEDIUM'
        elif percentage >= 50:
            return 'LOW'
        else:
            return 'NONE'
    
    def _assess_statement_concern(
        self,
        statement: str,
        percentage: float
    ) -> str:
        """
        Assess concern for statement concentration.
        
        'other' concentration is less concerning than main statements.
        """
        if statement == 'other':
            if percentage >= 90:
                return 'LOW'
            else:
                return 'NONE'
        else:
            return self._assess_concern_level(percentage)
    
    def _assess_temporal_concern(self, unknown_pct: float) -> str:
        """Assess concern for temporal pattern."""
        if unknown_pct >= 50:
            return 'HIGH'
        elif unknown_pct >= 30:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _interpret_namespace_pattern(
        self,
        namespace: str,
        percentage: float
    ) -> str:
        """Generate interpretation of namespace pattern."""
        if percentage >= 90:
            return f"Nearly all gaps from {namespace} - possible taxonomy coverage issue"
        elif percentage >= 70:
            return f"Most gaps from {namespace} - review taxonomy handling"
        else:
            return "Gaps distributed across taxonomies - no systematic issue"
    
    def _interpret_property_pattern(
        self,
        missing_prop: str,
        percentage: float
    ) -> str:
        """Generate interpretation of property pattern."""
        if percentage >= 90:
            return f"Nearly all gaps missing {missing_prop} - systematic extraction issue"
        elif percentage >= 70:
            return f"Most gaps missing {missing_prop} - review property extractor"
        else:
            return "Varied missing properties - no single root cause"
    
    def _interpret_statement_pattern(
        self,
        statement: str,
        percentage: float
    ) -> str:
        """Generate interpretation of statement pattern."""
        if statement == 'other' and percentage >= 70:
            return "Most gaps are supplementary data - expected behavior"
        elif percentage >= 90:
            return f"Nearly all gaps should be {statement} - classifier logic issue"
        elif percentage >= 70:
            return f"Most gaps should be {statement} - review classifier"
        else:
            return "Gaps distributed across statements - no pattern"
    
    def _interpret_temporal_pattern(
        self,
        instant_pct: float,
        duration_pct: float,
        unknown_pct: float
    ) -> str:
        """Generate interpretation of temporal pattern."""
        if unknown_pct >= 50:
            return "High percentage missing period_type - property extraction issue"
        elif instant_pct >= 80:
            return "Mostly instant facts unclassified - review instant handling"
        elif duration_pct >= 80:
            return "Mostly duration facts unclassified - review duration handling"
        else:
            return "Balanced temporal distribution - no systematic issue"
    
    def _build_empty_patterns(self) -> Dict[str, Any]:
        """Build empty pattern result."""
        return {
            'namespace_concentration': {'detected': False, 'concern_level': 'NONE'},
            'property_concentration': {'detected': False, 'concern_level': 'NONE'},
            'statement_concentration': {'detected': False, 'concern_level': 'NONE'},
            'temporal_concentration': {'detected': False, 'concern_level': 'NONE'},
            'gap_type_distribution': {}
        }


__all__ = ['GapPatternDetector']