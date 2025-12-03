# File: engines/ccq_mapper/analysis/gap_analyzer.py

"""
CCQ Gap Analyzer
================

Comprehensive gap analysis coordinator that orchestrates:
- Gap identification (which facts have gaps?)
- Gap characterization (what are the gaps?)
- Pattern detection (systematic issues?)
- Prioritization (which gaps matter most?)

Integrates GapIdentifier, GapPatternAnalyzer, GapRecommendationGenerator,
GapCharacterizer, GapPatternDetector, and GapPrioritizer to provide 
complete gap analysis with gaps.json output.

Architecture: Market-agnostic gap analysis.

REFACTORED VERSION:
This analyzer now delegates to specialized components while maintaining
backward compatibility with the existing API.
"""

from typing import Dict, Any, List
from core.system_logger import get_logger

# New specialized components
from .gap_identifier import GapIdentifier
from .gap_pattern_analyzer import GapPatternAnalyzer
from .gap_recommendation_generator import GapRecommendationGenerator

logger = get_logger(__name__)


class GapAnalyzer:
    """
    Comprehensive gap analysis coordinator.
    
    Responsibilities:
    - Identify unclassified facts
    - Coordinate comprehensive characterization
    - Detect systematic patterns
    - Prioritize gaps by importance
    - Generate actionable recommendations
    
    Does NOT:
    - Modify classifications
    - Make classification decisions
    - Access database
    """
    
    def __init__(
        self,
        statement_classifier=None,
        monetary_classifier=None,
        temporal_classifier=None
    ):
        """
        Initialize gap analyzer with sub-components.
        
        Args:
            statement_classifier: StatementClassifier instance (optional)
            monetary_classifier: MonetaryClassifier instance (optional)
            temporal_classifier: TemporalClassifier instance (optional)
        """
        self.logger = logger
        
        # Store classifiers for passing to characterizer
        self._statement_classifier = statement_classifier
        self._monetary_classifier = monetary_classifier
        self._temporal_classifier = temporal_classifier
        
        # Initialize basic analysis components (NEW)
        self.identifier = GapIdentifier()
        self.pattern_analyzer = GapPatternAnalyzer()
        self.recommendation_generator = GapRecommendationGenerator()
        
        # Initialize comprehensive analysis components (existing)
        try:
            from .gap_characterizer import GapCharacterizer
            self.logger.info(
                f"Attempting to initialize GapCharacterizer with classifiers: "
                f"statement={statement_classifier}, monetary={monetary_classifier}, "
                f"temporal={temporal_classifier}"
            )
            self.characterizer = GapCharacterizer(
                statement_classifier=statement_classifier,
                monetary_classifier=monetary_classifier,
                temporal_classifier=temporal_classifier
            )
            self.logger.info("Gap characterizer initialized successfully")
        except Exception as e:
            import traceback
            self.logger.error(f"CRITICAL: Gap characterizer initialization FAILED: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.characterizer = None
        
        try:
            from .gap_pattern_detector import GapPatternDetector
            self.pattern_detector = GapPatternDetector()
            self.logger.info("Gap pattern detector initialized")
        except Exception as e:
            self.logger.warning(f"Gap pattern detector unavailable: {e}")
            self.pattern_detector = None
        
        try:
            from .gap_prioritizer import GapPrioritizer
            self.prioritizer = GapPrioritizer()
            self.logger.info("Gap prioritizer initialized")
        except Exception as e:
            self.logger.warning(f"Gap prioritizer unavailable: {e}")
            self.prioritizer = None
        
        self.logger.info("Gap analyzer initialized with all components")
    
    def analyze_gaps(
        self,
        classified_facts: List[Dict[str, Any]],
        clusters: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Analyze classification gaps.
        
        Args:
            classified_facts: List of all classified facts
            clusters: Dictionary of clustered facts
            
        Returns:
            Gap analysis report dictionary with:
            - total_facts: Total number of facts
            - gap_count: Number of facts with gaps
            - gap_percentage: Percentage of facts with gaps
            - patterns: Basic pattern analysis
            - missing_properties: Missing properties analysis
            - recommendations: Actionable recommendations
            - gap_facts_sample: Sample of gap facts
            - enriched_gaps: Enriched gap profiles (if characterizer available)
            - comprehensive_patterns: Comprehensive patterns (if detector available)
            - prioritization: Gap prioritization (if prioritizer available)
        """
        self.logger.info("Analyzing classification gaps...")
        
        # Step 1: Identify unclassified or ambiguous facts
        gap_facts = self.identifier.identify_gap_facts(classified_facts)
        
        if not gap_facts:
            self.logger.info("✓ No classification gaps detected")
            return self._build_empty_report(len(classified_facts))
        
        # Step 2: Analyze patterns in gap facts
        patterns = self.pattern_analyzer.analyze_gap_patterns(gap_facts)
        
        # Step 3: Analyze missing properties
        missing_properties = self.pattern_analyzer.analyze_missing_properties(gap_facts)
        
        # Step 4: Generate recommendations
        recommendations = self.recommendation_generator.generate_recommendations(
            patterns,
            missing_properties
        )
        
        # Step 5: Build basic report
        report = self._build_gap_report(
            gap_facts,
            classified_facts,
            patterns,
            missing_properties,
            recommendations
        )
        
        # Step 6: Add comprehensive analysis using existing components
        enriched_gaps = []
        comprehensive_patterns = {}
        prioritization = {}
        
        if self.characterizer:
            try:
                self.logger.info(f"Starting gap characterization for {len(gap_facts)} facts")
                enriched_gaps = self.characterizer.characterize_gaps(gap_facts)
                self.logger.info(f"Characterized {len(enriched_gaps)} gaps")
            except Exception as e:
                import traceback
                self.logger.error(f"CRITICAL: Gap characterization FAILED during execution: {e}")
                self.logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            self.logger.error("CRITICAL: Characterizer is None, skipping comprehensive analysis")
        
        if self.pattern_detector and enriched_gaps:
            try:
                comprehensive_patterns = self.pattern_detector.detect_patterns(enriched_gaps)
                self.logger.info("Pattern detection complete")
            except Exception as e:
                self.logger.error(f"Pattern detection failed: {e}")
        
        if self.prioritizer and enriched_gaps:
            try:
                prioritization = self.prioritizer.prioritize_gaps(enriched_gaps)
                self.logger.info("Gap prioritization complete")
            except Exception as e:
                self.logger.error(f"Gap prioritization failed: {e}")
        
        # Add comprehensive analysis to report
        if enriched_gaps:
            report['enriched_gaps'] = enriched_gaps
        if comprehensive_patterns:
            report['comprehensive_patterns'] = comprehensive_patterns
        if prioritization:
            report['prioritization'] = prioritization
        
        self._log_gap_summary(report)
        
        return report
    
    def _build_gap_report(
        self,
        gap_facts: List[Dict[str, Any]],
        all_facts: List[Dict[str, Any]],
        patterns: Dict[str, Any],
        missing_properties: Dict[str, Any],
        recommendations: List[str]
    ) -> Dict[str, Any]:
        """
        Build comprehensive gap analysis report.
        
        Args:
            gap_facts: Facts with gaps
            all_facts: All classified facts
            patterns: Pattern analysis
            missing_properties: Missing properties analysis
            recommendations: Generated recommendations
            
        Returns:
            Gap analysis report dictionary
        """
        gap_count = len(gap_facts)
        total_count = len(all_facts)
        
        return {
            'total_facts': total_count,
            'gap_count': gap_count,
            'gap_percentage': round(gap_count / total_count * 100, 2) if total_count > 0 else 0.0,
            'patterns': patterns,
            'missing_properties': missing_properties,
            'recommendations': recommendations,
            'gap_facts_sample': [
                {
                    'concept': gf['fact'].get('concept', 'unknown'),
                    'gap_type': gf['gap_type'],
                    'reason': gf['reason']
                }
                for gf in gap_facts[:20]  # First 20
            ]
        }
    
    def _build_empty_report(self, total_facts: int) -> Dict[str, Any]:
        """
        Build empty report when no gaps found.
        
        Args:
            total_facts: Total number of facts
            
        Returns:
            Empty gap report with success message
        """
        return {
            'total_facts': total_facts,
            'gap_count': 0,
            'gap_percentage': 0.0,
            'patterns': {},
            'missing_properties': {},
            'recommendations': [self.recommendation_generator.generate_success_recommendation()],
            'gap_facts_sample': []
        }
    
    def _log_gap_summary(self, report: Dict[str, Any]) -> None:
        """
        Log gap analysis summary.
        
        Args:
            report: Gap analysis report
        """
        gap_count = report['gap_count']
        
        if gap_count == 0:
            self.logger.info("✓ No classification gaps detected")
            return
        
        gap_percentage = report['gap_percentage']
        
        self.logger.warning(f"\nClassification Gap Analysis:")
        self.logger.warning(f"  Total gaps: {gap_count} ({gap_percentage:.1f}%)")
        
        patterns = report.get('patterns', {})
        gap_type_counts = patterns.get('gap_type_counts', {})
        
        for gap_type, count in gap_type_counts.items():
            self.logger.warning(f"  - {gap_type}: {count}")
        
        self.logger.warning(f"\nRecommendations:")
        for rec in report['recommendations']:
            self.logger.warning(f"  {rec}")


__all__ = ['GapAnalyzer']