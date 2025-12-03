"""
Duplicate Detection Constants
==============================

Location: ccq_val/engines/ccq_mapper/analysis/duplicate_constants.py

Constants and configuration for duplicate detection.

Constants:
- Severity thresholds
- Display limits
- Severity level identifiers
- Field name mappings
"""

# Severity thresholds (variance as decimal, e.g., 0.05 = 5%)
CRITICAL_VARIANCE_THRESHOLD = 0.05  # 5% or more variance
MAJOR_VARIANCE_THRESHOLD = 0.01     # 1-5% variance
MINOR_VARIANCE_THRESHOLD = 0.0001   # 0.01-1% variance

# Display limits
MAX_DUPLICATES_DETAIL_LOG = 10
SEPARATOR_LENGTH = 80

# Severity levels
SEVERITY_CRITICAL = 'CRITICAL'
SEVERITY_MAJOR = 'MAJOR'
SEVERITY_MINOR = 'MINOR'
SEVERITY_REDUNDANT = 'REDUNDANT'

# Field name mappings for market-agnostic extraction
CONCEPT_FIELD_NAMES = [
    'concept_qname',
    'concept',
    'qname',
    'concept_local_name',
    'name'
]

CONTEXT_FIELD_NAMES = [
    'context_ref',
    'contextRef',
    'context_id'
]

VALUE_FIELD_NAMES = [
    'fact_value',
    'value',
    'amount'
]

# Severity descriptions for logging
SEVERITY_DESCRIPTIONS = {
    SEVERITY_CRITICAL: 'SEVERE DATA INTEGRITY ISSUES - Material variance >5%',
    SEVERITY_MAJOR: 'SIGNIFICANT DATA QUALITY CONCERNS - Notable variance 1-5%',
    SEVERITY_MINOR: 'Minor duplicate variances - Likely formatting/rounding',
    SEVERITY_REDUNDANT: 'Harmless redundant duplicates - No integrity concerns'
}