# File: engines/ccq_mapper/validation/property_null_analyzer.py

"""
CCQ Property Null Analyzer
===========================

Analyzes null values using CCQ's property-based classification approach.
Different from Map Pro's explanation-search method.

CCQ Strategy:
- Analyzes PROPERTIES of null facts
- Detects patterns in null distribution
- Validates against CCQ's own classifications
- No concept-search or text-explanation finding
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict

from core.system_logger import get_logger
from .null_quality_constants import (
    SUSPICION_NONE,
    SUSPICION_LOW,
    SUSPICION_MEDIUM,
    SUSPICION_HIGH,
    CLASSIFICATION_LEGITIMATE_NIL,
    CLASSIFICATION_EXPECTED_NULL,
    CLASSIFICATION_STRUCTURAL_NULL,
    CLASSIFICATION_ANOMALOUS_NULL
)

logger = get_logger(__name__)


class PropertyNullAnalyzer:
    """
    Analyzes nulls based on their properties and classification context.
    
    CCQ's Approach:
    - Check property completeness (unit, decimals, context)
    - Analyze classification confidence
    - Detect structural expectations
    - NO text-explanation searching
    """
    
    def __init__(self):
        """Initialize property null analyzer."""
        self.stats = {
            'total_nulls': 0,
            'legitimate_nils': 0,
            'expected_nulls': 0,
            'structural_nulls': 0,
            'anomalous_nulls': 0
        }
    
    def analyze_classified_fact(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a classified fact for null value.
        
        Args:
            fact: Original line item from CCQ mapping
            classification: CCQ's classification result
            
        Returns:
            Null analysis if value is null, None otherwise
        """
        value = fact.get('value')
        
        if not self._is_null_value(value):
            return None
        
        self.stats['total_nulls'] += 1
        
        # Check if explicitly nil in source
        if fact.get('properties', {}).get('is_nil'):
            return self._analyze_as_legitimate_nil(fact, classification)
        
        # Analyze based on properties
        return self._analyze_property_based_null(fact, classification)
    
    def _analyze_as_legitimate_nil(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze fact marked as nil in source XBRL."""
        self.stats['legitimate_nils'] += 1
        
        return {
            'qname': fact.get('qname'),
            'classification_type': CLASSIFICATION_LEGITIMATE_NIL,
            'suspicion_level': SUSPICION_NONE,
            'reason': 'Explicitly marked as nil in source XBRL',
            'properties': self._extract_relevant_properties(fact),
            'classification_context': {
                'statement': classification.get('statement'),
                'temporal_type': classification.get('temporal_type'),
                'confidence': classification.get('confidence', 0.0)
            }
        }
    
    def _analyze_property_based_null(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze null based on property expectations.
        
        CCQ Logic:
        1. Check if properties suggest value SHOULD exist
        2. Check if classification confidence is low (uncertain mapping)
        3. Check if null appears in expected statement section
        """
        properties = fact.get('properties', {})
        
        # Extract property signals
        has_unit = bool(fact.get('unit'))
        has_decimals = properties.get('decimals') is not None
        period_type = properties.get('period_type')
        
        # Classification context
        stmt_classification = classification.get('statement')
        temporal_classification = classification.get('temporal_type')
        classification_confidence = classification.get('confidence', 0.0)
        
        # Decision logic
        if self._is_expected_null(properties, classification):
            return self._classify_as_expected(fact, classification)
        
        elif self._is_structural_null(fact, classification):
            return self._classify_as_structural(fact, classification)
        
        else:
            return self._classify_as_anomalous(fact, classification)
    
    def _is_expected_null(
        self,
        properties: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> bool:
        """
        Check if null is expected based on properties.
        
        Examples:
        - Text/abstract elements (not monetary)
        - Low classification confidence (<0.5)
        - Disclosure/note elements
        """
        # Non-monetary items can be null
        if not properties.get('period_type'):
            return True
        
        # Low confidence classifications might not have values
        if classification.get('confidence', 1.0) < 0.5:
            return True
        
        # Abstract or parent elements
        if properties.get('is_abstract', False):
            return True
        
        return False
    
    def _is_structural_null(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> bool:
        """
        Check if null is due to structural position.
        
        Examples:
        - Optional disclosure items
        - Items that only appear in certain contexts
        - Supplementary data points
        """
        qname = fact.get('qname', '')
        
        # Disclosure namespaces (dei, ecd) often have nulls
        if qname.startswith('dei:') or qname.startswith('ecd:'):
            return True
        
        # Aggregation level suggests optional
        agg_level = classification.get('aggregation_level')
        if agg_level in ['subtotal', 'detail']:
            return True
        
        return False
    
    def _classify_as_expected(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Classify as expected null."""
        self.stats['expected_nulls'] += 1
        
        return {
            'qname': fact.get('qname'),
            'classification_type': CLASSIFICATION_EXPECTED_NULL,
            'suspicion_level': SUSPICION_LOW,
            'reason': self._determine_expected_reason(fact, classification),
            'properties': self._extract_relevant_properties(fact),
            'classification_context': self._extract_classification_context(classification)
        }
    
    def _classify_as_structural(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Classify as structural null."""
        self.stats['structural_nulls'] += 1
        
        return {
            'qname': fact.get('qname'),
            'classification_type': CLASSIFICATION_STRUCTURAL_NULL,
            'suspicion_level': SUSPICION_LOW,
            'reason': self._determine_structural_reason(fact, classification),
            'properties': self._extract_relevant_properties(fact),
            'classification_context': self._extract_classification_context(classification)
        }
    
    def _classify_as_anomalous(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Classify as anomalous null - requires attention."""
        self.stats['anomalous_nulls'] += 1
        
        # Determine suspicion level
        suspicion = self._determine_suspicion_level(fact, classification)
        
        return {
            'qname': fact.get('qname'),
            'classification_type': CLASSIFICATION_ANOMALOUS_NULL,
            'suspicion_level': suspicion,
            'reason': self._determine_anomaly_reason(fact, classification),
            'properties': self._extract_relevant_properties(fact),
            'classification_context': self._extract_classification_context(classification),
            'requires_review': suspicion in [SUSPICION_HIGH, SUSPICION_MEDIUM]
        }
    
    def _determine_suspicion_level(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> str:
        """Determine suspicion level for anomalous null."""
        properties = fact.get('properties', {})
        
        # High suspicion: Monetary fact in core statement with no value
        if (properties.get('period_type') == 'instant' and
            classification.get('statement') == 'balance_sheet' and
            classification.get('aggregation_level') == 'total'):
            return SUSPICION_HIGH
        
        # Medium suspicion: Expected monetary value missing
        if properties.get('period_type') in ['instant', 'duration']:
            return SUSPICION_MEDIUM
        
        return SUSPICION_LOW
    
    def _determine_expected_reason(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> str:
        """Determine reason for expected null."""
        properties = fact.get('properties', {})
        
        if properties.get('is_abstract'):
            return "Abstract/parent element (no direct value expected)"
        
        if classification.get('confidence', 1.0) < 0.5:
            return f"Low classification confidence ({classification.get('confidence', 0):.2f})"
        
        if not properties.get('period_type'):
            return "Non-temporal element (text or metadata)"
        
        return "Properties suggest null is expected"
    
    def _determine_structural_reason(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> str:
        """Determine reason for structural null."""
        qname = fact.get('qname', '')
        
        if qname.startswith('dei:'):
            return "Document/Entity Information (cover page metadata)"
        
        if qname.startswith('ecd:'):
            return "Executive Compensation Disclosure (supplementary)"
        
        agg_level = classification.get('aggregation_level')
        if agg_level:
            return f"Aggregation level '{agg_level}' - optional detail"
        
        return "Structural position suggests optional value"
    
    def _determine_anomaly_reason(
        self,
        fact: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> str:
        """Determine reason for anomalous null."""
        properties = fact.get('properties', {})
        stmt = classification.get('statement', 'unknown')
        
        reasons = []
        
        if properties.get('period_type'):
            reasons.append(f"Expected value in {stmt}")
        
        if fact.get('unit'):
            reasons.append("Has unit but no value")
        
        if classification.get('confidence', 0.0) > 0.7:
            reasons.append("High classification confidence but null")
        
        return "; ".join(reasons) if reasons else "Unexplained null value"
    
    def _extract_relevant_properties(self, fact: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant properties for analysis."""
        properties = fact.get('properties', {})
        
        return {
            'period_type': properties.get('period_type'),
            'balance_type': properties.get('balance_type'),
            'is_abstract': properties.get('is_abstract', False),
            'is_nil': properties.get('is_nil', False),
            'has_unit': bool(fact.get('unit')),
            'has_decimals': properties.get('decimals') is not None
        }
    
    def _extract_classification_context(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Extract classification context."""
        return {
            'statement': classification.get('statement'),
            'temporal_type': classification.get('temporal_type'),
            'monetary_type': classification.get('monetary_type'),
            'aggregation_level': classification.get('aggregation_level'),
            'confidence': classification.get('confidence', 0.0)
        }
    
    def _is_null_value(self, value: Any) -> bool:
        """Check if value is null."""
        return value is None or value == '' or value == 'None'
    
    def get_statistics(self) -> Dict[str, int]:
        """Get analysis statistics."""
        return self.stats.copy()
    
    def reset_statistics(self) -> None:
        """Reset statistics."""
        for key in self.stats:
            self.stats[key] = 0


__all__ = ['PropertyNullAnalyzer']