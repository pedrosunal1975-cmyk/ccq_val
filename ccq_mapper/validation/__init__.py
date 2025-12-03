# File: engines/ccq_mapper/validation/__init__.py

"""
CCQ Mapper Validation Module
=============================

Property-based null quality validation and statement comparison for CCQ Mapper.

Components:

Null Quality Validation:
- NullQualityValidator: Main orchestrator
- PropertyNullAnalyzer: Analyzes nulls via properties
- PatternDetector: Detects null patterns
- NullQualityScorer: Calculates quality scores
- Constants: Centralized thresholds and messages

Statement Comparison:
- StatementComparator: Main comparison coordinator
- FinancialStatementComparator: Financial statement comparisons
- QualityReportComparator: Quality report comparisons
- ComparisonEngine: Shared comparison utilities
"""

# Null Quality Validation
from .null_quality_validator import (
    NullQualityValidator,
    create_null_quality_validator
)
from .property_null_analyzer import PropertyNullAnalyzer
from .pattern_detector import PatternDetector
from .null_quality_scorer import NullQualityScorer
from .null_quality_constants import (
    SCORE_EXCELLENT_THRESHOLD,
    SCORE_GOOD_THRESHOLD,
    SCORE_ACCEPTABLE_THRESHOLD,
    SCORE_POOR_THRESHOLD,
    GRADE_EXCELLENT,
    GRADE_GOOD,
    GRADE_ACCEPTABLE,
    GRADE_POOR,
    GRADE_CRITICAL,
    SUSPICION_NONE,
    SUSPICION_LOW,
    SUSPICION_MEDIUM,
    SUSPICION_HIGH,
    CLASSIFICATION_LEGITIMATE_NIL,
    CLASSIFICATION_EXPECTED_NULL,
    CLASSIFICATION_STRUCTURAL_NULL,
    CLASSIFICATION_ANOMALOUS_NULL
)

# Statement Comparison
from .statement_comparator import StatementComparator
from .financial_statement_comparator import FinancialStatementComparator
from .quality_report_comparator import QualityReportComparator
from .comparison_engine import ComparisonEngine

__all__ = [
    # Null Quality Validation - Main validator
    'NullQualityValidator',
    'create_null_quality_validator',
    
    # Null Quality Validation - Core components
    'PropertyNullAnalyzer',
    'PatternDetector',
    'NullQualityScorer',
    
    # Null Quality Validation - Constants
    'SCORE_EXCELLENT_THRESHOLD',
    'SCORE_GOOD_THRESHOLD',
    'SCORE_ACCEPTABLE_THRESHOLD',
    'SCORE_POOR_THRESHOLD',
    'GRADE_EXCELLENT',
    'GRADE_GOOD',
    'GRADE_ACCEPTABLE',
    'GRADE_POOR',
    'GRADE_CRITICAL',
    'SUSPICION_NONE',
    'SUSPICION_LOW',
    'SUSPICION_MEDIUM',
    'SUSPICION_HIGH',
    'CLASSIFICATION_LEGITIMATE_NIL',
    'CLASSIFICATION_EXPECTED_NULL',
    'CLASSIFICATION_STRUCTURAL_NULL',
    'CLASSIFICATION_ANOMALOUS_NULL',
    
    # Statement Comparison - Main interface
    'StatementComparator',
    
    # Statement Comparison - Specialized comparators
    'FinancialStatementComparator',
    'QualityReportComparator',
    'ComparisonEngine'
]