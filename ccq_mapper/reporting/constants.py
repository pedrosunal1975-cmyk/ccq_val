# File: engines/ccq_mapper/reporting/constants.py

"""
CCQ Mapper Reporting Constants
===============================

Centralized constants for mapper reporting and logging.
Eliminates magic numbers and provides consistent formatting.
"""

# Display formatting
LOG_SEPARATOR_LENGTH = 80
SECTION_SEPARATOR = "=" * LOG_SEPARATOR_LENGTH
SUBSECTION_SEPARATOR = "-" * LOG_SEPARATOR_LENGTH

# Display limits
MAX_DISPLAY_ITEMS = 20
MAX_DISPLAY_DETAILS = 10
MAX_DISPLAY_PATTERNS = 10
MAX_DISPLAY_GAPS = 20
MAX_DISPLAY_DUPLICATES = 10

# Log level mapping for different event types
LOG_LEVEL_MAPPING = {
    'phase_start': 'INFO',
    'phase_complete': 'INFO',
    'classification_complete': 'INFO',
    'clustering_complete': 'INFO',
    'construction_complete': 'INFO',
    'validation_complete': 'INFO',
    'success': 'INFO',
    'warning': 'WARNING',
    'error': 'ERROR',
    'critical_duplicate': 'ERROR',
    'major_duplicate': 'WARNING',
    'low_confidence': 'WARNING',
    'gap_detected': 'WARNING',
    'null_quality_issue': 'WARNING'
}

# Report section identifiers
REPORT_SECTIONS = {
    'HEADER': 'header',
    'SUMMARY': 'summary',
    'CLASSIFICATION': 'classification',
    'CLUSTERING': 'clustering',
    'CONSTRUCTION': 'construction',
    'VALIDATION': 'validation',
    'QUALITY': 'quality',
    'DUPLICATES': 'duplicates',
    'GAPS': 'gaps',
    'SUCCESS': 'success',
    'RECOMMENDATIONS': 'recommendations',
    'FOOTER': 'footer'
}

# Success level colors (for terminal output if needed)
SUCCESS_LEVEL_SYMBOLS = {
    'EXCELLENT': '✓✓✓',
    'GOOD': '✓✓',
    'ACCEPTABLE': '✓',
    'POOR': '⚠',
    'FAILURE': '✗'
}

# Classification dimension labels
CLASSIFICATION_DIMENSIONS = {
    'monetary_type': 'Monetary Type',
    'temporal_type': 'Temporal Type',
    'accounting_type': 'Accounting Type',
    'aggregation_level': 'Aggregation Level',
    'predicted_statement': 'Statement Type'
}

# Confidence level labels
CONFIDENCE_LEVELS = {
    'high': 'High Confidence (≥85%)',
    'medium': 'Medium Confidence (70-85%)',
    'low': 'Low Confidence (<70%)'
}

# Duplicate severity labels
DUPLICATE_SEVERITY_LABELS = {
    'CRITICAL': '🔴 CRITICAL',
    'MAJOR': '🟠 MAJOR',
    'MINOR': '🟡 MINOR',
    'REDUNDANT': '🟢 REDUNDANT'
}

# Gap type labels
GAP_TYPE_LABELS = {
    'missing_classification': 'Missing Classification',
    'incomplete_classification': 'Incomplete Classification',
    'low_confidence': 'Low Confidence',
    'ambiguous': 'Ambiguous Classification'
}

# Success messages
MSG_SUCCESS_NO_DUPLICATES = "[OK] No duplicate facts detected in source XBRL"
MSG_SUCCESS_NO_GAPS = "[OK] No classification gaps detected"
MSG_SUCCESS_EXCELLENT = "[SUCCESS] Excellent mapping quality achieved"
MSG_SUCCESS_GOOD = "[SUCCESS] Good mapping quality achieved"
MSG_SUCCESS_ACCEPTABLE = "[INFO] Acceptable mapping quality - minor issues detected"

# Warning messages
MSG_WARNING_LOW_CONFIDENCE = "[WARNING] Low average classification confidence"
MSG_WARNING_GAPS_DETECTED = "[WARNING] Classification gaps detected"
MSG_WARNING_MAJOR_DUPLICATES = "[WARNING] Major duplicate facts with variance detected"
MSG_WARNING_LOW_COMPLETENESS = "[WARNING] Low classification completeness"

# Error messages
MSG_ERROR_CRITICAL_DUPLICATES = "[ERROR] CRITICAL duplicate facts with material variance"
MSG_ERROR_CLASSIFICATION_FAILURE = "[ERROR] Poor classification quality"
MSG_ERROR_PROCESSING_FAILED = "[ERROR] Mapping processing failed"

# Info messages
MSG_INFO_METADATA_EXCLUDED = "[INFO] Metadata facts excluded from mapping"
MSG_INFO_PATTERNS_DETECTED = "[INFO] Classification patterns detected"
MSG_INFO_RECOMMENDATIONS_AVAILABLE = "[INFO] Recommendations available for improvement"

# Formatting templates
TEMPLATE_PHASE_START = ">>> Starting phase: {phase}"
TEMPLATE_PHASE_COMPLETE = "<<< Completed phase: {phase} ({duration:.2f}s)"
TEMPLATE_CLASSIFICATION_SUMMARY = "Classification: {classified}/{total} facts ({rate:.1f}%)"
TEMPLATE_CONFIDENCE_SUMMARY = "Confidence: Avg {avg:.2f}, High: {high}, Medium: {medium}, Low: {low}"
TEMPLATE_DUPLICATE_SUMMARY = "Duplicates: {total} groups found ({percentage:.1f}% of facts)"
TEMPLATE_GAP_SUMMARY = "Gaps: {count} facts ({percentage:.1f}%)"
TEMPLATE_SUCCESS_SUMMARY = "Overall Score: {score:.1f}/100 ({level})"

# Decimal precision for displays
DISPLAY_PRECISION = {
    'percentage': 2,
    'confidence': 4,
    'score': 2,
    'time': 2,
    'variance': 2
}

__all__ = [
    'LOG_SEPARATOR_LENGTH',
    'SECTION_SEPARATOR',
    'SUBSECTION_SEPARATOR',
    'MAX_DISPLAY_ITEMS',
    'MAX_DISPLAY_DETAILS',
    'MAX_DISPLAY_PATTERNS',
    'MAX_DISPLAY_GAPS',
    'MAX_DISPLAY_DUPLICATES',
    'LOG_LEVEL_MAPPING',
    'REPORT_SECTIONS',
    'SUCCESS_LEVEL_SYMBOLS',
    'CLASSIFICATION_DIMENSIONS',
    'CONFIDENCE_LEVELS',
    'DUPLICATE_SEVERITY_LABELS',
    'GAP_TYPE_LABELS',
    'MSG_SUCCESS_NO_DUPLICATES',
    'MSG_SUCCESS_NO_GAPS',
    'MSG_SUCCESS_EXCELLENT',
    'MSG_SUCCESS_GOOD',
    'MSG_SUCCESS_ACCEPTABLE',
    'MSG_WARNING_LOW_CONFIDENCE',
    'MSG_WARNING_GAPS_DETECTED',
    'MSG_WARNING_MAJOR_DUPLICATES',
    'MSG_WARNING_LOW_COMPLETENESS',
    'MSG_ERROR_CRITICAL_DUPLICATES',
    'MSG_ERROR_CLASSIFICATION_FAILURE',
    'MSG_ERROR_PROCESSING_FAILED',
    'MSG_INFO_METADATA_EXCLUDED',
    'MSG_INFO_PATTERNS_DETECTED',
    'MSG_INFO_RECOMMENDATIONS_AVAILABLE',
    'TEMPLATE_PHASE_START',
    'TEMPLATE_PHASE_COMPLETE',
    'TEMPLATE_CLASSIFICATION_SUMMARY',
    'TEMPLATE_CONFIDENCE_SUMMARY',
    'TEMPLATE_DUPLICATE_SUMMARY',
    'TEMPLATE_GAP_SUMMARY',
    'TEMPLATE_SUCCESS_SUMMARY',
    'DISPLAY_PRECISION'
]