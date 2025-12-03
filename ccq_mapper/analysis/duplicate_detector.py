"""
CCQ Mapper Duplicate Detector - Main Orchestrator
==================================================

Location: ccq_val/engines/ccq_mapper/analysis/duplicate_detector.py

Detects and analyzes duplicate facts in source XBRL filings.
Adapted from Map Pro's duplicate detector for CCQ's property-based architecture.

Critical Purpose:
- Identify data integrity issues in XBRL filings
- Flag filings with material duplicate conflicts
- Provide severity classification for quality assessment
- Act as early warning system for unreliable financial data

Architecture: Market-agnostic duplicate detection for all XBRL sources.

Severity Levels:
- CRITICAL: Same concept+context, material variance (>5%) - severe data integrity issue
- MAJOR: Same concept+context, significant variance (1-5%) - needs review
- MINOR: Same concept+context, small variance (<1%) - likely rounding/formatting
- REDUNDANT: Same concept+context, exact same value - harmless duplicate

This is a WARNING system, not a blocker - mapper continues processing.

Components:
- duplicate_constants: Constants and thresholds
- fact_extractor: Market-agnostic field extraction
- fact_grouper: Groups facts by concept+context
- variance_calculator: Calculates variance and severity
- duplicate_analyzer_helper: Analyzes individual duplicates
- duplicate_report_builder: Builds comprehensive reports
- duplicate_logger_util: Logging utilities

Usage:
    # Standard usage (backward compatible)
    detector = DuplicateDetector()
    report = detector.analyze_duplicates(
        parsed_facts,
        parsed_metadata,
        xbrl_path=xbrl_file,
        parsed_facts_path=facts_file
    )
"""

from typing import Dict, Any, List
from pathlib import Path

from core.system_logger import get_logger

# Import refactored components
from .duplicate_constants import *
from .fact_grouper import (
    group_facts_by_concept_and_context,
    find_duplicate_groups
)
from .duplicate_analyzer_helper import analyze_duplicate_groups
from .duplicate_report_builder import (
    build_duplicate_report,
    build_empty_report
)
from .duplicate_logger_util import (
    log_duplicate_summary,
    log_analysis_start,
    log_analysis_complete
)

logger = get_logger(__name__)


class DuplicateDetector:
    """
    Detects duplicate facts in source XBRL filings for CCQ mapper.
    
    Responsibilities:
    - Identify facts with same concept + context
    - Calculate variance between duplicate values
    - Classify severity of duplicates
    - Generate duplicate analysis report
    - Provide warnings for quality assessment
    
    Does NOT:
    - Block mapper processing
    - Modify facts or database
    - Make market-specific assumptions
    
    This class orchestrates specialized components while maintaining
    full backward compatibility with existing code.
    """
    
    def __init__(self):
        """Initialize duplicate detector with components."""
        self.logger = logger
        
        # Import source tracer dynamically to avoid circular imports
        try:
            from .duplicate_source_tracer import DuplicateSourceTracer
            self.source_tracer = DuplicateSourceTracer()
            self.logger.info(
                "Duplicate source tracer initialized successfully"
            )
        except ImportError as e:
            self.logger.error(
                f"Source tracer import failed - "
                f"source attribution disabled: {e}"
            )
            self.source_tracer = None
        except Exception as e:
            self.logger.error(f"Source tracer initialization failed: {e}")
            self.source_tracer = None
        
        # Import duplicate analyzer dynamically
        try:
            from .duplicate_analyzer import DuplicateAnalyzer
            self.duplicate_analyzer = DuplicateAnalyzer()
            self.logger.info("Duplicate analyzer initialized successfully")
        except ImportError as e:
            self.logger.warning(
                f"Duplicate analyzer import failed - "
                f"detailed analysis disabled: {e}"
            )
            self.duplicate_analyzer = None
        except Exception as e:
            self.logger.warning(
                f"Duplicate analyzer initialization failed: {e}"
            )
            self.duplicate_analyzer = None
        
        self.logger.info("CCQ Duplicate detector initialized")
    
    def analyze_duplicates(
        self,
        parsed_facts: List[Dict[str, Any]],
        parsed_metadata: Dict[str, Any],
        xbrl_path: Path = None,
        parsed_facts_path: Path = None
    ) -> Dict[str, Any]:
        """
        Analyze parsed facts for duplicates with source attribution.
        
        Args:
            parsed_facts: List of facts from source XBRL (from parsed_facts.json)
            parsed_metadata: Metadata from parsing (filing info)
            xbrl_path: Optional path to raw XBRL file for source tracing
            parsed_facts_path: Optional path to parsed facts JSON
            
        Returns:
            Duplicate analysis report dictionary with source attribution
        """
        log_analysis_start(len(parsed_facts))
        
        # Group facts by concept + context
        fact_groups = group_facts_by_concept_and_context(parsed_facts)
        
        # Find duplicates (groups with >1 fact)
        duplicate_groups = find_duplicate_groups(fact_groups)
        
        if not duplicate_groups:
            log_analysis_complete(0)
            return build_empty_report(len(parsed_facts))
        
        log_analysis_complete(len(duplicate_groups))
        
        # Analyze each duplicate group
        duplicate_findings = analyze_duplicate_groups(duplicate_groups)
        
        # Trace duplicate sources if tracer available and paths provided
        source_report = self._trace_duplicate_sources(
            xbrl_path,
            parsed_facts_path,
            parsed_facts,
            duplicate_groups
        )
        
        # Perform comprehensive duplicate analysis if analyzer available
        comprehensive_analysis = self._perform_comprehensive_analysis(
            duplicate_groups,
            parsed_facts,
            source_report
        )
        
        # Build comprehensive report
        report = build_duplicate_report(
            duplicate_findings,
            len(parsed_facts),
            parsed_metadata,
            source_report,
            comprehensive_analysis
        )
        
        # Log summary
        log_duplicate_summary(report)
        
        return report
    
    def _trace_duplicate_sources(
        self,
        xbrl_path: Path,
        parsed_facts_path: Path,
        parsed_facts: List[Dict[str, Any]],
        duplicate_groups: Dict
    ) -> Dict[str, Any]:
        """
        Trace duplicate sources if tracer available.
        
        Args:
            xbrl_path: Path to raw XBRL file
            parsed_facts_path: Path to parsed facts JSON
            parsed_facts: List of parsed facts
            duplicate_groups: Duplicate fact groups
            
        Returns:
            Source report or None if tracing failed
        """
        if not self.source_tracer:
            return None
        
        if not (xbrl_path and parsed_facts_path):
            return None
        
        try:
            source_report = self.source_tracer.trace_duplicate_sources(
                xbrl_path,
                parsed_facts_path,
                parsed_facts,
                duplicate_groups
            )
            return source_report
        except Exception as e:
            self.logger.error(f"Source tracing failed: {e}")
            return None
    
    def _perform_comprehensive_analysis(
        self,
        duplicate_groups: Dict,
        parsed_facts: List[Dict[str, Any]],
        source_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive duplicate analysis if analyzer available.
        
        Args:
            duplicate_groups: Duplicate fact groups
            parsed_facts: List of parsed facts
            source_report: Source tracing report
            
        Returns:
            Comprehensive analysis or None if analysis failed
        """
        if not self.duplicate_analyzer:
            return None
        
        try:
            comprehensive_analysis = self.duplicate_analyzer.analyze(
                duplicate_groups,
                parsed_facts,
                source_report
            )
            self.logger.info("Comprehensive duplicate analysis complete")
            return comprehensive_analysis
        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed: {e}")
            return None
    
    # ========================================================================
    # BACKWARD COMPATIBILITY METHODS
    # ========================================================================
    # These methods preserve the original interface for existing code
    
    def _group_facts_by_concept_and_context(
        self,
        facts: List[Dict[str, Any]]
    ) -> Dict:
        """Group facts (backward compatibility - delegates to fact_grouper)."""
        return group_facts_by_concept_and_context(facts)
    
    def _extract_concept(self, fact: Dict[str, Any]) -> str:
        """Extract concept (backward compatibility - delegates to fact_extractor)."""
        from .fact_extractor import extract_concept
        return extract_concept(fact)
    
    def _extract_context(self, fact: Dict[str, Any]) -> str:
        """Extract context (backward compatibility - delegates to fact_extractor)."""
        from .fact_extractor import extract_context
        return extract_context(fact)
    
    def _analyze_duplicate_groups(self, duplicate_groups: Dict) -> List:
        """Analyze groups (backward compatibility - delegates to analyzer_helper)."""
        return analyze_duplicate_groups(duplicate_groups)
    
    def _analyze_single_duplicate(
        self,
        concept: str,
        context: str,
        facts: List
    ) -> Dict:
        """Analyze single duplicate (backward compatibility)."""
        from .duplicate_analyzer_helper import analyze_single_duplicate
        return analyze_single_duplicate(concept, context, facts)
    
    def _extract_values(self, facts: List) -> List:
        """Extract values (backward compatibility - delegates to fact_extractor)."""
        from .fact_extractor import extract_values
        return extract_values(facts)
    
    def _calculate_variance(self, values: List) -> tuple:
        """Calculate variance (backward compatibility - delegates to calculator)."""
        from .variance_calculator import calculate_variance
        return calculate_variance(values)
    
    def _classify_severity(self, variance_pct: float, unique_values: List) -> str:
        """Classify severity (backward compatibility - delegates to calculator)."""
        from .variance_calculator import classify_severity
        return classify_severity(variance_pct, unique_values)
    
    def _build_duplicate_report(
        self,
        findings: List,
        total_facts: int,
        metadata: Dict,
        source_report: Dict = None,
        comprehensive_analysis: Dict = None
    ) -> Dict:
        """Build report (backward compatibility - delegates to report_builder)."""
        return build_duplicate_report(
            findings,
            total_facts,
            metadata,
            source_report,
            comprehensive_analysis
        )
    
    def _count_by_severity(self, findings: List) -> Dict:
        """Count by severity (backward compatibility)."""
        from .duplicate_report_builder import calculate_severity_counts
        return calculate_severity_counts(findings)
    
    def _generate_quality_assessment(self, severity_counts: Dict) -> str:
        """Generate assessment (backward compatibility)."""
        from .duplicate_report_builder import generate_quality_assessment
        return generate_quality_assessment(severity_counts)
    
    def _build_empty_report(self, total_facts: int) -> Dict:
        """Build empty report (backward compatibility)."""
        return build_empty_report(total_facts)
    
    def _log_duplicate_summary(self, report: Dict):
        """Log summary (backward compatibility - delegates to logger_util)."""
        log_duplicate_summary(report)


__all__ = ['DuplicateDetector']