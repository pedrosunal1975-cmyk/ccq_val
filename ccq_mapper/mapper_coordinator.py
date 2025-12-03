# File: engines/ccq_mapper/mapper_coordinator.py

"""
CCQ Mapper Coordinator
=====================

Main orchestrator for property-based classification mapping with comprehensive
analysis and reporting.

CRITICAL DESIGN PRINCIPLE:
This mapper is STRUCTURALLY DIFFERENT from Map Pro's approach.
- NO concept index building
- NO fact-to-concept matching
- NO search operations
- START with facts, END with taxonomy validation + comprehensive reporting

REFACTORED VERSION:
This coordinator now delegates to specialized orchestrators and processors,
maintaining backward compatibility while improving code organization.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import time

from core.system_logger import get_logger
from core.data_paths import CCQPaths
from core.config_loader import ConfigLoader

# Orchestrators
from .orchestration.phase_orchestrator import PhaseOrchestrator
from .orchestration.data_loader import DataLoader
from .orchestration.property_processor import PropertyProcessor
from .orchestration.classification_processor import ClassificationProcessor
from .orchestration.clustering_processor import ClusteringProcessor
from .orchestration.analysis_orchestrator import AnalysisOrchestrator
from .orchestration.output_writer import OutputWriter

# Construction
from .construction.statement_constructor import StatementConstructor

# Validation
from .validation.taxonomy_validator import TaxonomyValidator
from .validation.comparison_reporter import ComparisonReporter
from .validation.null_quality_validator import create_null_quality_validator

# Reporting
from .reporting.mapper_logger import get_mapper_logger
from .reporting.summary_generator import SummaryGenerator

logger = get_logger(__name__)


class CCQMapperCoordinator:
    """
    Property-based classification mapper coordinator with comprehensive analysis.
    
    Workflow (BOTTOM-UP with Analysis):
    1. Load raw facts (no concept index)
    2. **Analyze source XBRL for duplicates**
    3. Extract XBRL properties from each fact
    4. Classify facts by properties (no matching)
    5. **Track classification metrics**
    6. Cluster facts into natural groups
    7. Construct statements from clusters
    8. Validate null quality
    9. **Analyze classification gaps**
    10. **Calculate success metrics**
    11. Write ALL outputs (statements + null_quality.json)
    12. Validate against taxonomy (AFTER construction)
    13. Generate comparison report
    14. **Generate executive summary**
    15. **Generate comprehensive reporting**
    """
    
    def __init__(self):
        """Initialize CCQ mapper coordinator with orchestrators."""
        self.logger = logger
        
        # Initialize configuration and paths
        self.config = ConfigLoader()
        self.paths = CCQPaths(
            data_root=self.config.get('data_root'),
            input_path=self.config.get('input_path'),
            output_path=self.config.get('output_path'),
            taxonomy_path=self.config.get('taxonomy_path'),
            parsed_facts_path=self.config.get('parsed_facts_path'),
            mapper_xbrl_path=self.config.get('mapper_xbrl_path'),
            mapper_output_path=self.config.get('mapper_output_path'),
            ccq_logs_path=self.config.get('ccq_logs_path'),
            mapper_logs_path=self.config.get('mapper_logs_path')
        )
        
        # Core processors
        self.data_loader = DataLoader()
        self.property_processor = PropertyProcessor()
        self.classification_processor = ClassificationProcessor()
        self.clustering_processor = ClusteringProcessor()
        
        # Construction and validation
        self.statement_constructor = StatementConstructor()
        self.taxonomy_validator = TaxonomyValidator()
        self.comparison_reporter = ComparisonReporter()
        self.null_quality_validator = create_null_quality_validator()
        
        # Analysis orchestrator (initialized after classification_processor)
        self.analysis_orchestrator = AnalysisOrchestrator(
            statement_classifier=self.classification_processor.get_statement_classifier(),
            monetary_classifier=self.classification_processor.get_monetary_classifier(),
            temporal_classifier=self.classification_processor.get_temporal_classifier()
        )
        
        # Output and reporting
        self.output_writer = OutputWriter(self.paths)
        self.summary_generator = SummaryGenerator()
        
        self.logger.info(
            "CCQ Mapper initialized with orchestrators and processors"
        )
    
    def map_filing(
        self,
        filing_id: str,
        xbrl_path: Path,
        parsed_facts_path: Path,
        taxonomy_paths: List[Path]
    ) -> Dict[str, Any]:
        """
        Map a filing using property-based classification with comprehensive analysis.
        
        Args:
            filing_id: Filing identifier
            xbrl_path: Path to raw XBRL filing
            parsed_facts_path: Path to parsed facts JSON
            taxonomy_paths: Paths to taxonomy files
            
        Returns:
            Mapping result dictionary with statements, validation, and analysis
        """
        # Initialize filing-specific components
        mapper_logger = get_mapper_logger(filing_id=filing_id)
        phase_orch = PhaseOrchestrator(filing_id)
        
        mapper_logger.log_info(f"Starting CCQ mapping for filing: {filing_id}")
        start_time = time.time()
        
        try:
            # Phase 1: Load all inputs
            facts, contexts, metadata = phase_orch.execute_phase(
                'load',
                lambda: self.data_loader.load_all_inputs(
                    xbrl_path, parsed_facts_path, taxonomy_paths
                ),
                facts_loaded=lambda: len(facts) if 'facts' in locals() else 0,
                contexts_loaded=lambda: len(contexts) if 'contexts' in locals() else 0
            )
            
            # Phase 2: Analyze source XBRL for duplicates
            duplicate_report = phase_orch.execute_phase(
                'duplicate_analysis',
                lambda: self.analysis_orchestrator.analyze_duplicates(
                    facts, metadata, xbrl_path, parsed_facts_path
                )
            )
            mapper_logger.log_duplicate_analysis(duplicate_report)
            
            # Phase 3: Extract properties (NO MATCHING)
            enriched_facts = phase_orch.execute_phase(
                'extract',
                lambda: self.property_processor.extract_properties(facts, contexts),
                facts_enriched=lambda: len(enriched_facts) if 'enriched_facts' in locals() else 0
            )
            
            # Phase 4: Classify facts (NO CONCEPT MATCHING)
            classified_facts, metrics_report = phase_orch.execute_phase(
                'classify',
                lambda: self.classification_processor.classify_facts(enriched_facts),
                facts_classified=lambda: len(classified_facts) if 'classified_facts' in locals() else 0
            )
            
            # Log classification summary
            summary = metrics_report.get('summary', {})
            mapper_logger.log_classification_summary(
                total_facts=summary.get('total_facts', 0),
                classified_facts=summary.get('classified_facts', 0),
                classification_rate=summary.get('classification_rate', 0.0)
            )
            
            # Phase 5: Cluster into natural groups
            clusters = phase_orch.execute_phase(
                'cluster',
                lambda: self.clustering_processor.cluster_facts(classified_facts),
                clusters_formed=lambda: len(clusters) if 'clusters' in locals() else 0
            )
            
            mapper_logger.log_clustering_summary(
                cluster_count=len(clusters),
                clustered_facts=sum(len(facts) for facts in clusters.values()),
                total_facts=len(classified_facts)
            )
            
            # Phase 6: Construct statements from clusters
            constructed_statements = phase_orch.execute_phase(
                'construct',
                lambda: self.statement_constructor.construct_statements(clusters, metadata),
                statements_constructed=lambda: len(constructed_statements) if 'constructed_statements' in locals() else 0
            )
            
            for statement in constructed_statements:
                mapper_logger.log_statement_construction(
                    statement_type=statement.get('statement_type', 'unknown'),
                    line_item_count=len(statement.get('line_items', []))
                )
            
            # Phase 7: Validate null quality
            null_quality_report = phase_orch.execute_phase(
                'null_quality',
                lambda: self.null_quality_validator.validate_statements(constructed_statements)
            )
            mapper_logger.log_null_quality_summary(null_quality_report)
            
            # Phase 8: Analyze classification gaps
            gap_analysis = phase_orch.execute_phase(
                'gap_analysis',
                lambda: self.analysis_orchestrator.analyze_gaps(classified_facts, clusters)
            )
            mapper_logger.log_gap_analysis(gap_analysis)
            
            # Phase 9: Calculate success metrics
            success_metrics = phase_orch.execute_phase(
                'success_calculation',
                lambda: self.analysis_orchestrator.calculate_success_metrics(
                    classified_facts=classified_facts,
                    clusters=clusters,
                    constructed_statements=constructed_statements,
                    classification_metrics=metrics_report,
                    gap_analysis=gap_analysis,
                    null_quality_report=null_quality_report,
                    duplicate_report=duplicate_report
                )
            )
            mapper_logger.log_success_summary(success_metrics)
            
            # Phase 10: Write ALL outputs
            statement_files = phase_orch.execute_phase(
                'write_outputs',
                lambda: self.output_writer.write_all_outputs(
                    constructed_statements,
                    null_quality_report,
                    duplicate_report,
                    gap_analysis,
                    filing_id,
                    metadata
                ),
                files_written=lambda: len(statement_files) if 'statement_files' in locals() else 0
            )
            
            # Phase 11: Validate against taxonomy (AFTER construction)
            validation_results = phase_orch.execute_phase(
                'validate',
                lambda: self.taxonomy_validator.validate(constructed_statements, taxonomy_paths)
            )
            
            # Phase 12: Generate comparison report
            comparison_report = phase_orch.execute_phase(
                'comparison',
                lambda: self.comparison_reporter.generate_report(
                    constructed_statements, validation_results
                )
            )
            
            # Phase 13: Generate executive summary
            executive_summary = self.summary_generator.generate_executive_summary(
                filing_id=filing_id,
                success_metrics=success_metrics,
                classification_metrics=metrics_report,
                duplicate_report=duplicate_report,
                gap_analysis=gap_analysis,
                null_quality_report=null_quality_report
            )
            
            # Log executive summary to console
            mapper_logger.log_info("\n" + executive_summary)
            
            # Calculate total duration
            total_duration = time.time() - start_time
            mapper_logger.log_info(
                f"Mapping complete for {filing_id} in {total_duration:.2f}s"
            )
            
            return {
                'success': True,
                'filing_id': filing_id,
                'statements': constructed_statements,
                'null_quality': null_quality_report,
                'statement_files': statement_files,
                'validation': validation_results,
                'comparison': comparison_report,
                'duplicate_analysis': duplicate_report,
                'classification_metrics': metrics_report,
                'gap_analysis': gap_analysis,
                'success_metrics': success_metrics,
                'executive_summary': executive_summary,
                'statistics': self._collect_statistics(
                    facts, classified_facts, clusters,
                    constructed_statements, validation_results,
                    null_quality_report, success_metrics
                ),
                'phase_timings': phase_orch.get_phase_timings(),
                'total_duration': total_duration
            }
            
        except Exception as e:
            mapper_logger.log_error(e, phase='mapping')
            return {
                'success': False,
                'filing_id': filing_id,
                'error': str(e)
            }
    
    def _collect_statistics(
        self,
        facts: List[Dict[str, Any]],
        classified_facts: List[Dict[str, Any]],
        clusters: Dict[str, List[Dict[str, Any]]],
        constructed_statements: List[Dict[str, Any]],
        validation_results: Dict[str, Any],
        null_quality_report: Dict[str, Any],
        success_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect comprehensive processing statistics."""
        return {
            'total_facts': len(facts),
            'classified_facts': len(classified_facts),
            'clusters_formed': len(clusters),
            'statements_constructed': len(constructed_statements),
            'validation_pass_rate': validation_results.get('pass_rate', 0.0),
            'null_quality_score': null_quality_report.get('quality_score', {}).get('score', 0.0),
            'null_quality_grade': null_quality_report.get('quality_score', {}).get('grade', 'UNKNOWN'),
            'overall_success_score': success_metrics.get('overall_score', 0.0),
            'success_level': success_metrics.get('success_level', 'UNKNOWN'),
            'is_success': success_metrics.get('is_success', False)
        }


__all__ = ['CCQMapperCoordinator']