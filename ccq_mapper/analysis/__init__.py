"""
CCQ Mapper Analysis Subsystem
==============================

Location: ccq_val/engines/ccq_mapper/analysis/__init__.py

Provides comprehensive analysis capabilities for CCQ's property-based mapper.

Main Components (Orchestrators):
- DuplicateDetector: Detect duplicate facts in source XBRL
- DuplicateSourceTracer: Trace duplicates to their source (XBRL/parsing/mapping)
- DuplicateAnalyzer: Comprehensive duplicate characterization and analysis
- GapAnalyzer: Analyze classification gaps and ambiguities (orchestrator)
- ClassificationMetrics: Track classification statistics and patterns
- GapCharacterizer: Enrich gaps with detailed characterization
- GapPatternDetector: Detect systematic patterns in gaps
- GapPrioritizer: Prioritize gaps by financial importance
- SuccessCalculator: Calculate overall mapping success metrics

Duplicate Detection Components (refactored):
- duplicate_constants: Constants and thresholds
- fact_extractor: Market-agnostic field extraction
- fact_grouper: Groups facts by concept+context
- variance_calculator: Calculates variance and severity
- duplicate_analyzer_helper: Analyzes individual duplicates
- duplicate_report_builder: Builds comprehensive reports
- duplicate_logger_util: Logging utilities
- duplicate_pattern_detector: Detects duplicate patterns
- duplicate_risk_assessor: Assesses duplicate risk

Duplicate Analyzer Components (refactored):
- duplicate_property_extractor: Extracts properties for classification
- duplicate_significance_assessor: Assesses financial significance
- duplicate_summary_aggregator: Aggregates duplicate summaries

Gap Analyzer Components (NEW - refactored):
- gap_identifier: Identifies classification gaps
- gap_pattern_analyzer: Analyzes gap patterns
- gap_recommendation_generator: Generates gap recommendations

Success Calculation Components (refactored):
- success_constants: Success thresholds and constants
- classification_scorer: Scores classification effectiveness
- confidence_scorer: Scores classification confidence
- clustering_scorer: Scores clustering effectiveness
- statement_scorer: Scores statement construction
- overall_scorer: Calculates weighted overall score
- recommendation_generator: Generates actionable recommendations
- performance_reporter: Generates performance reports

Architecture: Market-agnostic analysis for all XBRL sources.

Usage:
    # Standard duplicate detection (unchanged)
    from engines.ccq_mapper.analysis import DuplicateDetector
    
    detector = DuplicateDetector()
    report = detector.analyze_duplicates(parsed_facts, metadata)
    
    # Standard duplicate analysis (unchanged)
    from engines.ccq_mapper.analysis import DuplicateAnalyzer
    
    analyzer = DuplicateAnalyzer(
        statement_classifier=stmt_classifier,
        monetary_classifier=mon_classifier,
        temporal_classifier=temp_classifier
    )
    analysis = analyzer.analyze(duplicate_groups, all_facts)
    
    # Standard gap analysis (unchanged)
    from engines.ccq_mapper.analysis import GapAnalyzer
    
    gap_analyzer = GapAnalyzer(
        statement_classifier=stmt_classifier,
        monetary_classifier=mon_classifier,
        temporal_classifier=temp_classifier
    )
    gap_report = gap_analyzer.analyze_gaps(classified_facts, clusters)
    
    # Standard success calculation (unchanged)
    from engines.ccq_mapper.analysis import SuccessCalculator
    
    calculator = SuccessCalculator()
    metrics = calculator.calculate_success(
        classified_facts, clusters, statements,
        classification_metrics, gap_analysis,
        null_quality_report, duplicate_report
    )
    
    # Using individual components (advanced usage)
    from engines.ccq_mapper.analysis import (
        # Duplicate components
        fact_grouper, 
        variance_calculator,
        DuplicatePropertyExtractor,
        DuplicateSignificanceAssessor,
        # Gap components
        GapIdentifier,
        GapPatternAnalyzer,
        GapRecommendationGenerator,
        # Success components
        ClassificationScorer, 
        ConfidenceScorer
    )
    
    # Use gap identification independently
    identifier = GapIdentifier()
    gaps = identifier.identify_gap_facts(classified_facts)
    
    # Use gap pattern analysis independently
    pattern_analyzer = GapPatternAnalyzer()
    patterns = pattern_analyzer.analyze_gap_patterns(gaps)
"""

# Main analysis components
from .duplicate_detector import DuplicateDetector
from .duplicate_source_tracer import DuplicateSourceTracer
from .duplicate_analyzer import DuplicateAnalyzer
from .classification_metrics import ClassificationMetrics
from .gap_analyzer import GapAnalyzer
from .gap_characterizer import GapCharacterizer
from .gap_pattern_detector import GapPatternDetector
from .gap_prioritizer import GapPrioritizer
from .success_calculator import SuccessCalculator, SuccessCalculationError

# Duplicate detection components (for modular use)
from . import duplicate_constants
from . import fact_extractor
from . import fact_grouper
from . import variance_calculator
from . import duplicate_analyzer_helper
from . import duplicate_report_builder
from . import duplicate_logger_util

# Duplicate analyzer components (for modular use)
from .duplicate_property_extractor import DuplicatePropertyExtractor
from .duplicate_significance_assessor import (
    DuplicateSignificanceAssessor,
    SIGNIFICANCE_HIGH,
    SIGNIFICANCE_MEDIUM,
    SIGNIFICANCE_LOW
)
from .duplicate_summary_aggregator import DuplicateSummaryAggregator

# Gap analyzer components (NEW - for modular use)
from .gap_identifier import GapIdentifier
from .gap_pattern_analyzer import GapPatternAnalyzer
from .gap_recommendation_generator import GapRecommendationGenerator

# Success calculation components (for modular use)
from . import success_constants
from .classification_scorer import ClassificationScorer
from .confidence_scorer import ConfidenceScorer
from .clustering_scorer import ClusteringScorer
from .statement_scorer import StatementScorer
from .overall_scorer import OverallScorer
from .recommendation_generator import RecommendationGenerator
from .performance_reporter import PerformanceReporter

__all__ = [
    # Main analysis components
    'DuplicateDetector',
    'DuplicateSourceTracer',
    'DuplicateAnalyzer',
    'ClassificationMetrics',
    'GapAnalyzer',
    'GapCharacterizer',
    'GapPatternDetector',
    'GapPrioritizer',
    'SuccessCalculator',
    'SuccessCalculationError',
    
    # Duplicate detection modules (for advanced usage)
    'duplicate_constants',
    'fact_extractor',
    'fact_grouper',
    'variance_calculator',
    'duplicate_analyzer_helper',
    'duplicate_report_builder',
    'duplicate_logger_util',
    
    # Duplicate analyzer modules (for advanced usage)
    'DuplicatePropertyExtractor',
    'DuplicateSignificanceAssessor',
    'DuplicateSummaryAggregator',
    'SIGNIFICANCE_HIGH',
    'SIGNIFICANCE_MEDIUM',
    'SIGNIFICANCE_LOW',
    
    # Gap analyzer modules (NEW - for advanced usage)
    'GapIdentifier',
    'GapPatternAnalyzer',
    'GapRecommendationGenerator',
    
    # Success calculation modules (for advanced usage)
    'success_constants',
    'ClassificationScorer',
    'ConfidenceScorer',
    'ClusteringScorer',
    'StatementScorer',
    'OverallScorer',
    'RecommendationGenerator',
    'PerformanceReporter',
]

__version__ = '5.0.0'