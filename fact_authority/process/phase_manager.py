# File: engines/fact_authority/process/phase_manager.py
# Path: engines/fact_authority/process/phase_manager.py

"""
Phase Manager
=============

Coordinates the three phases of fact_authority validation:
1. LOAD: Load statements, taxonomies, XBRL filings, duplicate reports
2. PROCESS: Reconcile, analyze, report
3. OUTPUT: Write validated statements and duplicate comparison

Each phase is independent and returns structured results.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from core.system_logger import get_logger
from core.data_paths import CCQPaths

logger = get_logger(__name__)


class PhaseManager:
    """
    Manages the three validation phases.
    
    Responsibilities:
        - Execute load phase (statements, taxonomies, filings, duplicates)
        - Execute process phase (reconciliation, analysis)
        - Execute output phase (write results)
        - Handle phase transitions and error propagation
    """
    
    def __init__(self, ccq_paths: CCQPaths):
        """
        Initialize phase manager.
        
        Args:
            ccq_paths: CCQPaths instance with all configured paths
        """
        self.ccq_paths = ccq_paths
        self.logger = logger
    
    def execute_validation(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str,
        write_output: bool = True
    ) -> Dict[str, Any]:
        """
        Execute all three validation phases.
        
        Args:
            market: Market type
            entity_name: Entity identifier (Map Pro's directory name)
            filing_type: Filing type
            filing_date: Filing date
            write_output: Whether to write output
            
        Returns:
            Dict with validation results or errors
        """
        # Phase 1: Load
        load_result = self._load_phase(
            market, entity_name, filing_type, filing_date
        )
        
        if not load_result['success']:
            return {
                'success': False,
                'errors': load_result.get('errors', []),
                'phase': 'load'
            }
        
        # Phase 2: Process
        process_result = self._process_phase(load_result['data'])
        
        if not process_result['success']:
            return {
                'success': False,
                'errors': process_result.get('errors', []),
                'phase': 'process'
            }
        
        # Phase 3: Output
        if write_output:
            output_result = self._output_phase(
                process_result['data'],
                market, entity_name, filing_type, filing_date
            )
            
            return {
                'success': True,
                'reconciliation_result': process_result['data']['reconciliation'],
                'report': process_result['data']['report'],
                'output_path': output_result.get('output_path'),
                'statistics': process_result['data'].get('statistics', {})
            }
        else:
            return {
                'success': True,
                'reconciliation_result': process_result['data']['reconciliation'],
                'report': process_result['data']['report'],
                'statistics': process_result['data'].get('statistics', {})
            }
    
    def _load_phase(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Dict[str, Any]:
        """
        Load all required data for validation.
        
        Steps:
            1. Load mapped statements from both mappers
            2. Load duplicate reports from both mappers (NEW)
            3. Load facts.json to identify taxonomies
            4. Load taxonomies using taxonomy_reader
            5. Load XBRL filing using filings_reader
            
        Args:
            market: Market type
            entity_name: Entity identifier (Map Pro's directory name)
            filing_type: Filing type
            filing_date: Filing date
            
        Returns:
            Dict with 'success' and 'data' or 'errors'
        """
        self.logger.info("PHASE 1: Loading data")
        
        try:
            from engines.fact_authority.input.statement_loader import StatementLoader
            from engines.fact_authority.input.duplicate_report_loader import DuplicateReportLoader
            from engines.fact_authority.facts_reader import ParsedFactsLoader
            from engines.fact_authority.taxonomy_reader import TaxonomyReader
            from engines.fact_authority.filings_reader import FilingReader
            from engines.fact_authority.process.taxonomy_detector import TaxonomyDetector
            
            data = {}
            
            # 1. Load mapped statements
            # Note: statement_loader handles name variations internally
            self.logger.info("Loading mapped statements...")
            statement_loader = StatementLoader(self.ccq_paths)
            
            map_pro_statements = statement_loader.load_map_pro_statements(
                market, entity_name, filing_type, filing_date
            )
            ccq_statements = statement_loader.load_ccq_statements(
                market, entity_name, filing_type, filing_date
            )
            
            data['map_pro_statements'] = map_pro_statements
            data['ccq_statements'] = ccq_statements
            
            # 2. Load duplicate reports (NEW)
            # Note: duplicate_report_loader handles name variations internally
            self.logger.info("Loading duplicate reports from both mappers...")
            duplicate_loader = DuplicateReportLoader()
            
            # Map Pro duplicates are in input_mapped (mapped_statements)
            map_pro_dir = Path(self.ccq_paths.input_mapped) / market / entity_name / filing_type / filing_date
            
            # CCQ duplicates are in mapper_output (ccq_mapped)
            # Pass entity_name - loader will search for name variations
            ccq_dir = Path(self.ccq_paths.mapper_output) / market / entity_name / filing_type / filing_date
            
            # Load reports - loader handles CCQ name variations automatically
            duplicate_reports = duplicate_loader.load_reports(
                map_pro_dir=map_pro_dir,
                ccq_dir=ccq_dir,
                entity_name=entity_name
            )
            
            data['duplicate_reports'] = duplicate_reports
            
            # Log duplicate summary
            comparison = duplicate_reports.get('comparison', {})
            if comparison and comparison.get('duplicates_in_both', 0) > 0:
                self.logger.info(
                    f"Duplicate analysis: {comparison.get('agreement_rate', 0):.1f}% agreement, "
                    f"cleaner mapper: {comparison.get('cleaner_mapper', 'unknown')}"
                )
            
            # 3. Load facts.json and detect taxonomies
            self.logger.info("Identifying taxonomies from facts.json...")
            facts_loader = ParsedFactsLoader(self.ccq_paths)
            facts_data = facts_loader.load_by_filing_info(
                market, entity_name, filing_type, filing_date
            )
            
            # Use TaxonomyDetector to extract namespaces
            detector = TaxonomyDetector()
            concepts = facts_loader.get_concepts(facts_data)
            namespaces = detector.extract_namespaces(concepts)
            primary_ns = detector.determine_primary_taxonomy(namespaces)
            
            data['namespaces'] = namespaces
            data['facts_data'] = facts_data
            data['primary_namespace'] = primary_ns
            
            self.logger.info(f"Primary taxonomy: {primary_ns}, All namespaces: {namespaces}")
            
            # 4. Load taxonomies
            self.logger.info("Loading taxonomies...")
            taxonomy_reader = TaxonomyReader()
            
            taxonomy_paths = self.ccq_paths.get_taxonomy_paths_for_filing(
                market=market,
                taxonomy_name=primary_ns
            )
            
            if not taxonomy_paths:
                self.logger.warning(f"No taxonomy paths found for {market}/{primary_ns}")
                taxonomy_data = {}
            else:
                taxonomy_data = taxonomy_reader.read_taxonomy(taxonomy_paths)
            
            data['taxonomy_data'] = taxonomy_data
            
            # 5. Load XBRL filing
            self.logger.info("Loading XBRL filing...")
            filing_reader = FilingReader(self.ccq_paths)
            
            filing_file = self.ccq_paths.find_xbrl_filing(
                market, entity_name, filing_type, filing_date
            )
            
            if not filing_file:
                self.logger.warning(f"XBRL filing not found")
                filing_data = {}
            else:
                filing_dir = filing_file.parent
                filing_data = filing_reader.read_filing(filing_dir)
            
            data['filing_data'] = filing_data
            
            self.logger.info("Load phase completed successfully")
            return {
                'success': True,
                'data': data
            }
            
        except FileNotFoundError as e:
            self.logger.error(f"Required file not found: {e}")
            return {
                'success': False,
                'errors': [f"File not found: {e}"]
            }
        except Exception as e:
            self.logger.error(f"Error in load phase: {e}", exc_info=True)
            return {
                'success': False,
                'errors': [str(e)]
            }
    
    def _process_phase(self, load_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process loaded data through reconciliation and analysis.
        
        Steps:
            1. Trace extension inheritance
            2. Enrich taxonomy with extensions
            3. Reconcile statements against taxonomy
            4. Analyze null quality
            5. Generate report (with duplicate metrics)
            
        Args:
            load_data: Data from load phase
            
        Returns:
            Dict with 'success' and 'data' or 'errors'
        """
        self.logger.info("PHASE 2: Processing data")
        
        try:
            from engines.fact_authority.process.statement_reconciler import StatementReconciler
            from engines.fact_authority.process.extension_inheritance_tracer import ExtensionInheritanceTracer
            from engines.fact_authority.process.null_quality_handler import NullQualityHandler
            from engines.fact_authority.output.reconciliation_reporter import ReconciliationReporter
            from engines.fact_authority.process.taxonomy_enricher import TaxonomyEnricher
            
            data = {}
            
            # 1. Trace extension concept inheritance
            extension_data = {}
            if load_data.get('filing_data') and load_data.get('taxonomy_data'):
                self.logger.info("Tracing extension concept inheritance...")
                tracer = ExtensionInheritanceTracer(self.ccq_paths)
                extension_data = tracer.trace_extensions(
                    load_data['filing_data'],
                    load_data['taxonomy_data']
                )
                
                self.logger.info(
                    f"Found {extension_data['statistics']['total_extensions']} extension concepts, "
                    f"{extension_data['statistics']['valid_inheritance']} with valid inheritance"
                )
            
            data['extension_data'] = extension_data
            
            # 2. Enrich taxonomy with extension mappings
            enricher = TaxonomyEnricher()
            enriched_taxonomy = enricher.enrich_taxonomy_with_extensions(
                load_data['taxonomy_data'],
                extension_data
            )
            
            # 3. Reconcile statements against enriched taxonomy
            self.logger.info("Reconciling statements against taxonomy...")
            reconciler = StatementReconciler(enriched_taxonomy, self.ccq_paths)
            
            reconciliation_result = reconciler.reconcile(
                load_data['map_pro_statements'],
                load_data['ccq_statements']
            )
            
            data['reconciliation'] = reconciliation_result
            
            # 4. Analyze null quality
            self.logger.info("Analyzing null quality...")
            null_handler = NullQualityHandler(self.ccq_paths)
            null_analysis = null_handler.analyze_from_statements(
                load_data['map_pro_statements'],
                load_data['ccq_statements']
            )
            
            data['null_analysis'] = null_analysis
            
            # 5. Generate report (now with duplicate metrics)
            self.logger.info("Generating reconciliation report...")
            reporter = ReconciliationReporter()
            report = reporter.generate_report(
                reconciliation_result,
                null_analysis,
                load_data.get('duplicate_reports')  # NEW: Pass duplicate reports
            )
            
            data['report'] = report
            data['statistics'] = reconciliation_result.get('overall_statistics', {})
            data['duplicate_reports'] = load_data.get('duplicate_reports')  # NEW: Pass through for output phase
            
            self.logger.info("Process phase completed successfully")
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            self.logger.error(f"Error in process phase: {e}", exc_info=True)
            return {
                'success': False,
                'errors': [str(e)]
            }
    
    def _output_phase(
        self,
        process_data: Dict[str, Any],
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Dict[str, Any]:
        """
        Write validated statements and reports to disk.
        
        Includes writing duplicate_comparison.json (NEW).
        
        Args:
            process_data: Data from process phase
            market: Market type
            entity_name: Entity identifier
            filing_type: Filing type
            filing_date: Filing date
            
        Returns:
            Dict with output path
        """
        self.logger.info("PHASE 3: Writing output")
        
        try:
            from engines.fact_authority.output.output_writer import OutputWriter
            
            writer = OutputWriter(self.ccq_paths)
            output_path = writer.write_validated_statements(
                process_data['reconciliation'],
                process_data['report'],
                process_data.get('null_analysis'),
                market, entity_name, filing_type, filing_date
            )
            
            # NEW: Write duplicate comparison report if available
            duplicate_reports = process_data.get('duplicate_reports')
            if duplicate_reports and duplicate_reports.get('comparison', {}).get('duplicates_in_both', 0) > 0:
                self._write_duplicate_comparison(
                    duplicate_reports,
                    output_path
                )
            
            self.logger.info(f"Output written to: {output_path}")
            return {
                'success': True,
                'output_path': output_path
            }
            
        except Exception as e:
            self.logger.error(f"Error in output phase: {e}", exc_info=True)
            return {
                'success': False,
                'errors': [str(e)]
            }
    
    def _write_duplicate_comparison(
        self,
        duplicate_reports: Dict[str, Any],
        output_dir: Path
    ) -> None:
        """
        Write duplicate_comparison.json to output directory.
        
        Args:
            duplicate_reports: Duplicate comparison data
            output_dir: Output directory path
        """
        import json
        
        output_file = output_dir / 'duplicate_comparison.json'
        
        try:
            # Prepare serializable data (convert sets to lists)
            serializable_data = self._prepare_duplicate_data_for_json(duplicate_reports)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Wrote duplicate comparison report to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to write duplicate comparison: {e}")
            # Don't fail the entire output phase for this
    
    def _prepare_duplicate_data_for_json(
        self,
        duplicate_reports: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert sets to lists for JSON serialization.
        
        Args:
            duplicate_reports: Raw duplicate reports with sets
            
        Returns:
            JSON-serializable dictionary
        """
        import json
        
        def convert_sets(obj):
            """Recursively convert sets to lists."""
            if isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, dict):
                return {k: convert_sets(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_sets(item) for item in obj]
            elif isinstance(obj, tuple):
                return list(obj)
            else:
                return obj
        
        return convert_sets(duplicate_reports)


__all__ = ['PhaseManager']