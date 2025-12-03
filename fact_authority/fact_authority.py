# File: engines/fact_authority/fact_authority.py
# Path: engines/fact_authority/fact_authority.py

"""
Fact Authority Engine - Main Orchestrator
==========================================

Main coordinator for fact_authority engine that validates mapper outputs
against taxonomy authority.

Architecture:
    TAXONOMY (via taxonomy_reader/)
            |
      SOURCE OF TRUTH
            |
    +-------+-------+
    |               |
Map Pro           CCQ
    |               |
Compare to    Compare to
 TAXONOMY      TAXONOMY

Workflow:
    1. LOAD: Statements, taxonomies, XBRL filings
    2. PROCESS: Reconcile against taxonomy, analyze
    3. OUTPUT: Write validated statements

Does NOT:
    - Load statements directly (statement_loader does)
    - Parse taxonomies (taxonomy_reader does)
    - Parse XBRL (filings_reader does)
    - Write files (output_writer does)
"""

from pathlib import Path
from typing import Dict, Any, Optional

from core.system_logger import get_logger
from core.data_paths import CCQPaths, initialize_paths

logger = get_logger(__name__)


class FactAuthority:
    """
    Main orchestrator for fact_authority validation engine.
    
    Coordinates all sub-engines and processing components to validate
    mapper outputs against taxonomy authority.
    
    Responsibilities:
        - Initialize paths and configuration
        - Coordinate workflow execution via PhaseManager
        - Handle errors and logging
        - Return validation results
    
    Does NOT:
        - Execute phases directly (PhaseManager does)
        - Load/process/write data (phase components do)
    """
    
    def __init__(self, ccq_paths: CCQPaths):
        """
        Initialize fact authority engine.
        
        Args:
            ccq_paths: CCQPaths instance with all configured paths
        """
        self.logger = logger
        self.ccq_paths = ccq_paths
        
        # Initialize global data_paths for components that use it
        initialize_paths({
            'data_root': str(ccq_paths.data_root),
            'input_path': str(ccq_paths.input_mapped),
            'output_path': str(ccq_paths.output_validated),
            'taxonomy_path': str(ccq_paths.taxonomies),
            'parsed_facts_path': str(ccq_paths.parsed_facts),
            'mapper_xbrl_path': str(ccq_paths.mapper_xbrl) if ccq_paths.mapper_xbrl else None,
            'mapper_output_path': str(ccq_paths.mapper_output) if ccq_paths.mapper_output else None,
            'ccq_logs_path': str(ccq_paths.ccq_logs) if ccq_paths.ccq_logs else None,
            'mapper_logs_path': str(ccq_paths.mapper_logs) if ccq_paths.mapper_logs else None,
            'unified_output_path': str(ccq_paths.unified_mapped) if ccq_paths.unified_mapped else None,
            'taxonomy_cache_path': str(ccq_paths.taxonomy_cache) if ccq_paths.taxonomy_cache else None,
            'filings_cache_path': str(ccq_paths.filings_cache) if ccq_paths.filings_cache else None
        })
        
        # Phase manager (initialized lazily)
        self._phase_manager = None
        
        self.logger.info("FactAuthority engine initialized")
    
    @property
    def phase_manager(self):
        """Lazy initialization of PhaseManager."""
        if self._phase_manager is None:
            from engines.fact_authority.process.phase_manager import PhaseManager
            self._phase_manager = PhaseManager(self.ccq_paths)
        return self._phase_manager
    
    def validate_filing(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str,
        write_output: bool = True
    ) -> Dict[str, Any]:
        """
        Validate a filing by reconciling mapper outputs against taxonomy.
        
        This is the main entry point for fact_authority validation.
        
        Name variations (e.g., VISA_INC. vs VISA_INC_) are handled automatically
        by statement_loader and duplicate_report_loader using NameNormalizer.
        
        Args:
            market: Market type ('sec', 'fca', 'esma')
            entity_name: Entity identifier (Map Pro's directory name)
            filing_type: Filing type ('10-K', '10-Q', etc.)
            filing_date: Filing date (YYYY-MM-DD)
            write_output: Whether to write validated statements to disk
            
        Returns:
            Dict containing:
                - success: bool
                - reconciliation_result: Dict with validated statements
                - report: Dict with reconciliation report
                - output_path: Path where statements were written (if written)
                - errors: List of errors (if any)
                
        Raises:
            FileNotFoundError: If required input files missing
            ValueError: If validation fails critically
        """
        self.logger.info(
            f"Starting validation: {market}/{entity_name}/{filing_type}/{filing_date}"
        )
        
        try:
            # Execute all phases via PhaseManager
            # Name variations handled automatically by loaders
            result = self.phase_manager.execute_validation(
                market=market,
                entity_name=entity_name,
                filing_type=filing_type,
                filing_date=filing_date,
                write_output=write_output
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Fatal error in validation: {e}", exc_info=True)
            return {
                'success': False,
                'errors': [str(e)],
                'phase': 'unknown'
            }


__all__ = ['FactAuthority']