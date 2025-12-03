# File: engines/ccq_mapper/analysis/duplicate_analyzer.py

"""
CCQ Duplicate Analyzer
======================

Comprehensive duplicate characterization system that enriches duplicates with
multi-dimensional classification.

Provides deep insights into WHAT is being duplicated:
- Statement type (Balance Sheet, Income, Cash Flow, Other)
- Value type (Currency, Shares, Pure, Text, Nil)
- Temporal type (Instant, Duration)
- Accounting type (Debit, Credit, Flow)
- Aggregation type (Total, Line Item)
- Financial significance
- Pattern detection
- Risk assessment

Architecture: Market-agnostic duplicate analysis for all XBRL sources.

CRITICAL: Uses property-based classification, not concept matching.
This enables cross-market, cross-taxonomy analysis.

REFACTORED VERSION:
This analyzer now delegates to specialized components while maintaining
backward compatibility with the existing API.
"""

from typing import Dict, Any, List, Tuple
from collections import defaultdict

from core.system_logger import get_logger

# Existing dependencies (unchanged)
from .duplicate_pattern_detector import DuplicatePatternDetector
from .duplicate_risk_assessor import DuplicateRiskAssessor

# New specialized components
from .duplicate_property_extractor import DuplicatePropertyExtractor
from .duplicate_significance_assessor import (
    DuplicateSignificanceAssessor,
    SIGNIFICANCE_HIGH,
    SIGNIFICANCE_MEDIUM,
    SIGNIFICANCE_LOW
)
from .duplicate_summary_aggregator import DuplicateSummaryAggregator

logger = get_logger(__name__)


class DuplicateAnalyzer:
    """
    Comprehensive duplicate analysis engine.
    
    Responsibilities:
    - Enrich duplicate profiles with multi-dimensional classification
    - Coordinate pattern detection (via DuplicatePatternDetector)
    - Coordinate risk assessment (via DuplicateRiskAssessor)
    - Generate detailed reports
    
    Does NOT:
    - Modify facts or data
    - Make decisions about duplicate handling
    - Access database directly
    """
    
    def __init__(
        self,
        statement_classifier=None,
        monetary_classifier=None,
        temporal_classifier=None,
        accounting_classifier=None,
        aggregation_classifier=None
    ):
        """
        Initialize duplicate analyzer with classifiers.
        
        Args:
            statement_classifier: StatementClassifier instance
            monetary_classifier: MonetaryClassifier instance
            temporal_classifier: TemporalClassifier instance
            accounting_classifier: AccountingClassifier instance
            aggregation_classifier: AggregationClassifier instance
        """
        self.logger = logger
        
        # Import and initialize classifiers
        self._initialize_classifiers(
            statement_classifier,
            monetary_classifier,
            temporal_classifier,
            accounting_classifier,
            aggregation_classifier
        )
        
        # Initialize helper components
        self.pattern_detector = DuplicatePatternDetector()
        self.risk_assessor = DuplicateRiskAssessor()
        
        # Initialize new specialized components
        self.property_extractor = DuplicatePropertyExtractor()
        self.significance_assessor = DuplicateSignificanceAssessor()
        self.summary_aggregator = DuplicateSummaryAggregator()
        
        self.logger.info("Duplicate analyzer initialized with all classifiers and components")
    
    def _initialize_classifiers(
        self,
        statement_classifier,
        monetary_classifier,
        temporal_classifier,
        accounting_classifier,
        aggregation_classifier
    ):
        """Initialize all classifiers with dynamic imports if needed."""
        if statement_classifier is None:
            import sys
            from pathlib import Path as P
            project_root = P(__file__).parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            from statement_classifier import StatementClassifier
            statement_classifier = StatementClassifier()
        
        if monetary_classifier is None:
            from monetary_classifier import MonetaryClassifier
            monetary_classifier = MonetaryClassifier()
        
        if temporal_classifier is None:
            from temporal_classifier import TemporalClassifier
            temporal_classifier = TemporalClassifier()
        
        if accounting_classifier is None:
            from accounting_classifier import AccountingClassifier
            accounting_classifier = AccountingClassifier()
        
        if aggregation_classifier is None:
            from aggregation_classifier import AggregationClassifier
            aggregation_classifier = AggregationClassifier()
        
        self.statement_classifier = statement_classifier
        self.monetary_classifier = monetary_classifier
        self.temporal_classifier = temporal_classifier
        self.accounting_classifier = accounting_classifier
        self.aggregation_classifier = aggregation_classifier
    
    def analyze(
        self,
        duplicate_groups: Dict[Tuple[str, str], List[Dict[str, Any]]],
        all_facts: List[Dict[str, Any]],
        source_attribution: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive duplicate analysis.
        
        Args:
            duplicate_groups: Dictionary of (concept, context) -> duplicate facts
            all_facts: Complete list of facts for property extraction
            source_attribution: Optional source attribution from DuplicateSourceTracer
            
        Returns:
            Comprehensive analysis report dictionary with:
            - total_duplicate_groups: Number of duplicate groups
            - total_duplicate_facts: Total duplicate facts
            - enriched_duplicates: List of enriched duplicate profiles
            - patterns: Detected patterns
            - summary_by_statement: Summary by statement type
            - summary_by_value_type: Summary by value type
            - summary_by_significance: Summary by significance level
            - risk_assessment: Risk assessment results
            - metadata: Analysis metadata
        """
        self.logger.info(f"Analyzing {len(duplicate_groups)} duplicate groups...")
        
        # Build fact lookup index for property extraction
        fact_index = self._build_fact_index(all_facts)
        
        # Enrich each duplicate group
        enriched_duplicates = []
        for (concept, context), facts in duplicate_groups.items():
            enriched = self._enrich_duplicate_group(
                concept,
                context,
                facts,
                fact_index,
                source_attribution
            )
            enriched_duplicates.append(enriched)
        
        # Detect patterns using pattern detector
        patterns = self.pattern_detector.detect_patterns(enriched_duplicates)
        
        # Generate summaries using summary aggregator
        summary_by_statement = self.summary_aggregator.summarize_by_statement(
            enriched_duplicates
        )
        summary_by_value_type = self.summary_aggregator.summarize_by_value_type(
            enriched_duplicates
        )
        summary_by_significance = self.summary_aggregator.summarize_by_significance(
            enriched_duplicates
        )
        
        # Assess risk using risk assessor
        risk_assessment = self.risk_assessor.assess_risk(
            enriched_duplicates,
            patterns
        )
        
        # Build comprehensive report
        report = {
            'total_duplicate_groups': len(duplicate_groups),
            'total_duplicate_facts': sum(len(facts) for facts in duplicate_groups.values()),
            'enriched_duplicates': enriched_duplicates,
            'patterns': patterns,
            'summary_by_statement': summary_by_statement,
            'summary_by_value_type': summary_by_value_type,
            'summary_by_significance': summary_by_significance,
            'risk_assessment': risk_assessment,
            'metadata': {
                'analyzer_version': '2.0',
                'total_facts_analyzed': len(all_facts)
            }
        }
        
        self.logger.info("Duplicate analysis complete")
        
        return report
    
    def _build_fact_index(
        self,
        facts: List[Dict[str, Any]]
    ) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """
        Build index of facts by (concept, context) for quick lookup.
        
        Args:
            facts: List of all facts
            
        Returns:
            Dictionary mapping (concept, context) to fact properties
        """
        index = {}
        
        for fact in facts:
            concept = self.property_extractor.extract_concept(fact)
            context = self.property_extractor.extract_context(fact)
            
            if concept and context:
                key = (concept, context)
                # Store first occurrence (they should all have same properties)
                if key not in index:
                    index[key] = fact
        
        return index
    
    def _enrich_duplicate_group(
        self,
        concept: str,
        context: str,
        duplicate_facts: List[Dict[str, Any]],
        fact_index: Dict[Tuple[str, str], Dict[str, Any]],
        source_attribution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich a single duplicate group with comprehensive classification.
        
        Args:
            concept: Concept identifier
            context: Context identifier
            duplicate_facts: List of duplicate facts
            fact_index: Fact lookup index
            source_attribution: Source attribution data
            
        Returns:
            Enriched duplicate profile with full classification
        """
        # Get fact properties for classification
        key = (concept, context)
        fact = fact_index.get(key, duplicate_facts[0] if duplicate_facts else {})
        
        # Extract properties using property extractor
        properties = self.property_extractor.extract_properties(fact)
        
        # Classify across all dimensions
        statement_type = self.statement_classifier.classify(properties)
        monetary_type = self.monetary_classifier.classify(properties)
        temporal_type = self.temporal_classifier.classify(properties)
        accounting_type = self.accounting_classifier.classify(properties)
        aggregation_type = self.aggregation_classifier.classify(properties)
        
        # Determine financial significance using significance assessor
        significance = self.significance_assessor.assess_significance(
            concept,
            statement_type,
            monetary_type,
            aggregation_type,
            properties
        )
        
        # Extract values and calculate variance
        values = [self.property_extractor.extract_value(f) for f in duplicate_facts]
        variance_pct, variance_amount = self._calculate_variance(values)
        
        # Find source attribution for this duplicate
        duplicate_source = self._find_source_attribution(
            concept,
            context,
            source_attribution
        )
        
        return {
            'concept': concept,
            'context': context[:80] + '...' if len(context) > 80 else context,
            'full_context': context,
            'duplicate_count': len(duplicate_facts),
            'values': values,
            'unique_values': list(set(str(v) for v in values if v is not None)),
            'variance_percentage': variance_pct,
            'variance_amount': variance_amount,
            
            # Multi-dimensional classification
            'classification': {
                'statement_type': statement_type,
                'monetary_type': monetary_type,
                'temporal_type': temporal_type,
                'accounting_type': accounting_type,
                'aggregation_type': aggregation_type,
                'is_primary_context': properties.get('is_primary_context', True),
                'value_type': properties.get('value_type', 'unknown')
            },
            
            # Financial significance
            'significance': significance,
            
            # Source attribution
            'source': duplicate_source,
            
            # Raw properties for debugging
            'properties': properties
        }
    
    def _calculate_variance(
        self,
        values: List[Any]
    ) -> Tuple[float, float]:
        """
        Calculate variance between values.
        
        Args:
            values: List of values
            
        Returns:
            Tuple of (variance_percentage, max_variance_amount)
        """
        if not values:
            return 0.0, 0.0
        
        # Filter out None values
        numeric_values = []
        for v in values:
            try:
                if v is not None:
                    numeric_values.append(float(v))
            except (ValueError, TypeError):
                continue
        
        if len(numeric_values) < 2:
            return 0.0, 0.0
        
        min_val = min(numeric_values)
        max_val = max(numeric_values)
        
        if min_val == 0 and max_val == 0:
            return 0.0, 0.0
        
        variance_amount = abs(max_val - min_val)
        
        # Calculate percentage variance
        base = max(abs(min_val), abs(max_val))
        if base > 0:
            variance_pct = (variance_amount / base) * 100
        else:
            variance_pct = 0.0
        
        return round(variance_pct, 2), variance_amount
    
    def _find_source_attribution(
        self,
        concept: str,
        context: str,
        source_attribution: Dict[str, Any]
    ) -> str:
        """
        Find source attribution for this duplicate.
        
        Args:
            concept: Concept identifier
            context: Context identifier
            source_attribution: Source attribution from tracer
            
        Returns:
            Source string ('SOURCE_DATA', 'MAPPING_INTRODUCED', 'UNKNOWN')
        """
        if not source_attribution:
            return 'UNKNOWN'
        
        # Look through source details for this specific duplicate
        source_details = source_attribution.get('source_details', [])
        
        for detail in source_details:
            if detail.get('concept') == concept and detail.get('context') == context:
                return detail.get('source', 'UNKNOWN')
        
        return 'UNKNOWN'


__all__ = [
    'DuplicateAnalyzer',
    'SIGNIFICANCE_HIGH',
    'SIGNIFICANCE_MEDIUM',
    'SIGNIFICANCE_LOW'
]