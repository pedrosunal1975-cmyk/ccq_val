# File: engines/ccq_mapper/validation/null_quality_constants.py

"""
CCQ Null Quality Constants
===========================

Constants for CCQ's property-based null quality validation.
Similar purpose to Map Pro's but aligned with CCQ's architecture.
"""

from typing import Set, List

# Quality score thresholds
SCORE_EXCELLENT_THRESHOLD: int = 95
SCORE_GOOD_THRESHOLD: int = 85
SCORE_ACCEPTABLE_THRESHOLD: int = 75
SCORE_POOR_THRESHOLD: int = 60

# Quality grades
GRADE_EXCELLENT: str = 'EXCELLENT'
GRADE_GOOD: str = 'GOOD'
GRADE_ACCEPTABLE: str = 'ACCEPTABLE'
GRADE_POOR: str = 'POOR'
GRADE_CRITICAL: str = 'CRITICAL'
GRADE_UNKNOWN: str = 'UNKNOWN'

# Score penalties (property-based)
PENALTY_ANOMALOUS_NULL: int = 3
PENALTY_HIGH_SUSPICION_NULL: int = 5
PENALTY_PATTERN_CLUSTER: int = 2

# Score bonuses (property-based)
BONUS_HIGH_LEGITIMATE_RATE: int = 5
HIGH_LEGITIMATE_THRESHOLD: float = 90.0

# Suspicion levels
SUSPICION_NONE: str = 'none'
SUSPICION_LOW: str = 'low'
SUSPICION_MEDIUM: str = 'medium'
SUSPICION_HIGH: str = 'high'

# Classification types (CCQ-specific)
CLASSIFICATION_LEGITIMATE_NIL: str = 'legitimate_nil'
CLASSIFICATION_EXPECTED_NULL: str = 'expected_null'
CLASSIFICATION_STRUCTURAL_NULL: str = 'structural_null'
CLASSIFICATION_ANOMALOUS_NULL: str = 'anomalous_null'

# Warning thresholds
HIGH_NULL_PERCENTAGE_THRESHOLD: float = 30.0
ANOMALOUS_NULL_WARNING_THRESHOLD: int = 5
LOW_LEGITIMATE_RATE_THRESHOLD: float = 50.0

# Pattern detection thresholds
PATTERN_CLUSTER_THRESHOLD: int = 5  # Nulls in same statement section
PATTERN_NAMESPACE_THRESHOLD: float = 80.0  # % nulls in same namespace
PATTERN_CONFIDENCE_THRESHOLD: float = 0.3  # Low confidence correlation

# Property expectations
EXPECTED_PROPERTIES_FOR_VALUE: Set[str] = {
    'period_type',
    'balance_type'
}

# Namespaces that commonly have nulls (legitimate)
NULLABLE_NAMESPACES: Set[str] = {
    'dei',  # Document/Entity Information
    'ecd',  # Executive Compensation Disclosure
    'srt'   # SEC Reporting Taxonomy
}

# Aggregation levels that may have nulls
NULLABLE_AGGREGATION_LEVELS: Set[str] = {
    'subtotal',
    'detail',
    'disclosure'
}

# Confidence thresholds for suspicion
LOW_CONFIDENCE_THRESHOLD: float = 0.5
HIGH_CONFIDENCE_THRESHOLD: float = 0.8

# Message templates
MSG_SUCCESS_NO_NULLS: str = "[SUCCESS] No null values in CCQ mapped statements"
MSG_WARNING_HIGH_NULL_PCT: str = "[WARNING] {statement_type} has {null_pct:.1f}% null values - review classification"
MSG_ACTION_PATTERN_DETECTED: str = "[ACTION] Pattern detected: {pattern_count} nulls in {pattern_type} - review classification logic"
MSG_ANOMALOUS_NULLS: str = "{count} anomalous null values found - manual review recommended"
MSG_HIGH_SUSPICION_NULLS: str = "{count} high-suspicion null values in core statements"
MSG_LOW_LEGITIMATE_RATE: str = "Low legitimate null rate ({rate:.1f}%) - possible classification issues"
MSG_LEGITIMATE_NILS: str = "{count} values explicitly nil in source XBRL (legitimate)"
MSG_EXPECTED_NULLS: str = "{count} null values expected based on properties"
MSG_STRUCTURAL_NULLS: str = "{count} null values due to structural position"

# Reason templates
REASON_LOW_CONFIDENCE: str = "Classification confidence below {threshold:.1f}"
REASON_ABSTRACT_ELEMENT: str = "Abstract or parent element"
REASON_OPTIONAL_DISCLOSURE: str = "Optional disclosure element"
REASON_METADATA_FIELD: str = "Metadata or cover page field"
REASON_PROPERTY_MISMATCH: str = "Property expectations not met"


__all__ = [
    'SCORE_EXCELLENT_THRESHOLD',
    'SCORE_GOOD_THRESHOLD',
    'SCORE_ACCEPTABLE_THRESHOLD',
    'SCORE_POOR_THRESHOLD',
    'GRADE_EXCELLENT',
    'GRADE_GOOD',
    'GRADE_ACCEPTABLE',
    'GRADE_POOR',
    'GRADE_CRITICAL',
    'GRADE_UNKNOWN',
    'SUSPICION_NONE',
    'SUSPICION_LOW',
    'SUSPICION_MEDIUM',
    'SUSPICION_HIGH',
    'CLASSIFICATION_LEGITIMATE_NIL',
    'CLASSIFICATION_EXPECTED_NULL',
    'CLASSIFICATION_STRUCTURAL_NULL',
    'CLASSIFICATION_ANOMALOUS_NULL',
    'EXPECTED_PROPERTIES_FOR_VALUE',
    'NULLABLE_NAMESPACES',
    'NULLABLE_AGGREGATION_LEVELS'
]