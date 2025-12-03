# File: engines/ccq_mapper/orchestration/analysis_orchestrator.py

"""
Analysis Orchestrator
=====================

Orchestrates all analysis operations (duplicates, gaps, success metrics).

Responsibility:
- Coordinate duplicate analysis
- Coordinate gap analysis
- Calculate success metrics
- Generate comprehensive reports
"""

from typing import Dict, Any, List
from pathlib import Path

from core.system_logger import get_logger
from ..analysis.duplicate_detector import DuplicateDetector
from ..analysis.gap_analyzer import GapAnalyzer
from ..analysis.success_calculator import SuccessCalculator

logger = get_logger(__name__)


class AnalysisOrchestrator:
    """Orchestrates comprehensive analysis operations."""
    
    def __init__(
        self,
        statement_classifier,
        monetary_classifier,
        temporal_classifier
    ):
        """
        Initialize analysis orchestrator.
        
        Args:
            statement_classifier: Statement classifier instance
            monetary_classifier: Monetary classifier instance
            temporal_classifier: Temporal classifier instance
        """
        self.duplicate_detector = DuplicateDetector()
        self.gap_analyzer = GapAnalyzer(
            statement_classifier=statement_classifier,
            monetary_classifier=monetary_classifier,
            temporal_classifier=temporal_classifier
        )
        self.success_calculator = SuccessCalculator()
        self.logger = logger
    
    def analyze_duplicates(
        self,
        facts: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        xbrl_path: Path,
        parsed_facts_path: Path
    ) -> Dict[str, Any]:
        """
        Analyze source XBRL for duplicates.
        
        Args:
            facts: List of facts to analyze
            metadata: Filing metadata
            xbrl_path: Path to raw XBRL
            parsed_facts_path: Path to parsed facts
            
        Returns:
            Duplicate analysis report
        """
        self.logger.info("Analyzing duplicates...")
        
        return self.duplicate_detector.analyze_duplicates(
            facts, metadata, xbrl_path, parsed_facts_path
        )
    
    def analyze_gaps(
        self,
        classified_facts: List[Dict[str, Any]],
        clusters: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Analyze classification gaps.
        
        Args:
            classified_facts: Classified facts
            clusters: Fact clusters
            
        Returns:
            Gap analysis report
        """
        self.logger.info("Analyzing classification gaps...")
        
        return self.gap_analyzer.analyze_gaps(classified_facts, clusters)
    
    def calculate_success_metrics(
        self,
        classified_facts: List[Dict[str, Any]],
        clusters: Dict[str, List[Dict[str, Any]]],
        constructed_statements: List[Dict[str, Any]],
        classification_metrics: Dict[str, Any],
        gap_analysis: Dict[str, Any],
        null_quality_report: Dict[str, Any],
        duplicate_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive success metrics.
        
        Args:
            classified_facts: Classified facts
            clusters: Fact clusters
            constructed_statements: Constructed statements
            classification_metrics: Classification metrics report
            gap_analysis: Gap analysis report
            null_quality_report: Null quality report
            duplicate_report: Duplicate analysis report
            
        Returns:
            Success metrics report
        """
        self.logger.info("Calculating success metrics...")
        
        return self.success_calculator.calculate_success(
            classified_facts=classified_facts,
            clusters=clusters,
            constructed_statements=constructed_statements,
            classification_metrics=classification_metrics,
            gap_analysis=gap_analysis,
            null_quality_report=null_quality_report,
            duplicate_report=duplicate_report
        )


__all__ = ['AnalysisOrchestrator']