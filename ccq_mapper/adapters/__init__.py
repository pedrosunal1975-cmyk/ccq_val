"""
Adapters Module
===============

Location: ccq_val/engines/ccq_mapper/adapters/__init__.py

Adapters for translating Map Pro and CCQ formats to neutral format.

Components:
- neutral_format: Common data structure for facts
- map_pro_adapter: Reads Map Pro JSON → Neutral format
- ccq_adapter: Reads CCQ JSON → Neutral format
- neutral_comparator: Compares neutral format facts
- error_analyzer: Analyzes adapter parsing errors (orchestrator)
- error_models: Data structures for error analysis
- error_categorizer: Error classification utilities
- map_pro_analyzer: Map Pro-specific error analysis
- ccq_analyzer: CCQ-specific error analysis
- error_reporter: Error report generation

Usage:
    # Basic adapter usage
    from engines.ccq_mapper.adapters import (
        NeutralFact,
        MapProAdapter,
        CCQAdapter,
        NeutralComparator
    )
    
    # Parse Map Pro
    map_pro_adapter = MapProAdapter()
    map_pro_facts = map_pro_adapter.parse_statement_file(
        Path("map_pro_balance_sheet.json")
    )
    
    # Parse CCQ
    ccq_adapter = CCQAdapter()
    ccq_facts = ccq_adapter.parse_statement_file(
        Path("ccq_balance_sheet.json")
    )
    
    # Compare
    comparator = NeutralComparator()
    results = comparator.compare(map_pro_facts, ccq_facts, "balance_sheet")
    
    # Error analysis
    from engines.ccq_mapper.adapters import ErrorAnalyzer
    
    analyzer = ErrorAnalyzer()
    summary = analyzer.analyze_map_pro_errors(
        Path("map_pro_balance_sheet.json"),
        "balance_sheet"
    )
"""

# Core neutral format
from .neutral_format import (
    NeutralFact,
    normalize_concept_id,
    extract_namespace,
    extract_local_name,
    extract_date_from_context_id,
    validate_neutral_fact
)

# Adapters
from .map_pro_adapter import MapProAdapter
from .ccq_adapter import CCQAdapter
from .neutral_comparator import NeutralComparator

# Error analysis components
from .error_models import ErrorDetail, ErrorSummary
from .error_categorizer import (
    extract_namespace as extract_ns,
    categorize_error,
    check_missing_fields_map_pro,
    check_missing_fields_ccq
)
from .map_pro_analyzer import MapProErrorAnalyzer
from .ccq_analyzer import CCQErrorAnalyzer
from .error_reporter import ErrorReporter

# Main error analyzer orchestrator
from .error_analyzer import ErrorAnalyzer

__all__ = [
    # Data structures
    'NeutralFact',
    'ErrorDetail',
    'ErrorSummary',
    
    # Core adapters
    'MapProAdapter',
    'CCQAdapter',
    'NeutralComparator',
    
    # Error analysis
    'ErrorAnalyzer',
    'MapProErrorAnalyzer',
    'CCQErrorAnalyzer',
    'ErrorReporter',
    
    # Utility functions
    'normalize_concept_id',
    'extract_namespace',
    'extract_local_name',
    'extract_date_from_context_id',
    'validate_neutral_fact',
    'categorize_error',
    'check_missing_fields_map_pro',
    'check_missing_fields_ccq',
]

__version__ = '2.0.0'