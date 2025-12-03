# File: core/ccq_coordinator.py
# Path: core/ccq_coordinator.py

"""
CCQ Coordinator (Revised Architecture)
=======================================

Main orchestrator for CCQ validation process.
Now handles both transformation AND validation.

REFACTORED: Delegates infrastructure concerns to helper classes:
- FilingMetadataParser: Parse metadata from paths
- StatementFileLoader: Load JSON statement files
- TaxonomyBuilder: Build taxonomy accessors
- ValidationPersister: Save results (files + DB)
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional

from core.system_logger import get_logger
from core.database_coordinator import DatabaseCoordinator
from core.filing_metadata_parser import FilingMetadataParser
from core.statement_file_loader import StatementFileLoader
from core.taxonomy_builder import TaxonomyBuilder
from core.validation_persister import ValidationPersister

# Phase 1: Normalization (Transformation)
from core.name_normalizer import NameNormalizer

# Phase 2: Validation
from engines.validation.vertical_checker import VerticalChecker
from engines.validation.horizontal_checker import HorizontalChecker
from engines.validation.anomaly_detector import AnomalyDetector

# Phase 3: Scoring
from engines.scoring.score_calculator import ScoreCalculator
from engines.scoring.report_generator import ReportGenerator

from shared.exceptions.ccq_exceptions import CCQError, ValidationError

logger = get_logger(__name__)


class CCQCoordinator:
    """
    Main CCQ validation coordinator.
    
    Orchestrates:
    - Statement loading (delegates to StatementFileLoader)
    - Data normalization
    - Validation checks
    - Scoring
    - Report generation
    - Result persistence (delegates to ValidationPersister)
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        db_coordinator: Optional[DatabaseCoordinator] = None
    ):
        """
        Initialize CCQ coordinator.
        
        Args:
            config: Configuration dictionary
            db_coordinator: Optional database coordinator (None to skip DB)
        """
        self.config = config
        self.logger = logger
        self.db_coordinator = db_coordinator
        
        # Validation components (initialized in initialize())
        self.normalizer: Optional[Normalizer] = None
        self.vertical_checker: Optional[VerticalChecker] = None
        self.horizontal_checker: Optional[HorizontalChecker] = None
        self.anomaly_detector: Optional[AnomalyDetector] = None
        self.score_calculator: Optional[ScoreCalculator] = None
        self.report_generator: Optional[ReportGenerator] = None
        
        # Helper components (initialized in initialize())
        self.metadata_parser: Optional[FilingMetadataParser] = None
        self.statement_loader: Optional[StatementFileLoader] = None
        self.taxonomy_builder: Optional[TaxonomyBuilder] = None
        self.validation_persister: Optional[ValidationPersister] = None
        
        self.initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize all CCQ components.
        
        Returns:
            True if successful
        """
        try:
            self.logger.info("Initializing CCQ components...")
            
            # Initialize validation components
            self.normalizer = Normalizer(self.config)
            self.vertical_checker = VerticalChecker(self.config)
            self.horizontal_checker = HorizontalChecker(self.config)
            self.anomaly_detector = AnomalyDetector(self.config)
            self.score_calculator = ScoreCalculator(self.config)
            self.report_generator = ReportGenerator(self.config)
            
            # Initialize helper components
            self.metadata_parser = FilingMetadataParser()
            self.statement_loader = StatementFileLoader()
            self.taxonomy_builder = TaxonomyBuilder(
                taxonomy_path=self.config.get('taxonomy_path')
            )
            self.validation_persister = ValidationPersister(
                report_generator=self.report_generator,
                db_coordinator=self.db_coordinator
            )
            
            self.initialized = True
            self.logger.info("CCQ coordinator initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"CCQ initialization failed: {e}", exc_info=True)
            return False
    
    async def validate_filing(self, filing_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Validate a filing's mapped statements.
        
        NOTE: This method is kept for backward compatibility but is not
        fully implemented. Use validate_filing_from_path() instead.
        
        Args:
            filing_id: Filing UUID
            force: Force reprocessing if already validated
            
        Returns:
            Validation result with confidence score
            
        Raises:
            NotImplementedError: This method needs a filing path
        """
        raise NotImplementedError(
            "validate_filing() requires a filing path. "
            "Use validate_filing_from_path() instead."
        )
    
    async def validate_filing_from_path(
        self,
        filing_path: Path,
        filing_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Validate a filing from its directory path.
        
        Args:
            filing_path: Path to filing directory containing JSON files
            filing_id: Generated filing identifier
            force: Force reprocessing
            
        Returns:
            Validation result dict
        """
        if not self.initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            self.logger.info(f"=== CCQ Validation Started: {filing_id} ===")
            
            # Parse filing metadata from path
            parsed_metadata = self.metadata_parser.parse_from_path(filing_path)
            self.logger.debug(f"Parsed filing metadata: {parsed_metadata}")
            
            # Load statement files
            loaded_data = self.statement_loader.load_statements_from_directory(
                filing_path
            )
            
            statements = loaded_data['statements']
            metadata = loaded_data['metadata']
            other_data = loaded_data['other_data']
            
            self.logger.info(
                f"Loaded {len(statements)} statements: {list(statements.keys())}"
            )
            
            # Wrap statements with metadata
            statements_with_meta = self.statement_loader.wrap_statements_with_metadata(
                statements, metadata
            )
            
            # Normalize statements
            normalized = await self.normalizer.normalize_all(statements_with_meta)
            
            self.logger.info(
                f"Normalized {normalized['stats']['facts_normalized']} facts"
            )
            
            # Build taxonomy accessor
            taxonomy_accessor = self.taxonomy_builder.build_taxonomy_accessor(
                normalized
            )
            
            # Run validation checks
            vertical_results = await self.vertical_checker.check_all(
                normalized['statements'],
                taxonomy_accessor=taxonomy_accessor
            )
            
            self.logger.info(
                f"Vertical checks: {vertical_results['summary']['passed']}/"
                f"{vertical_results['summary']['total']} passed"
            )
            
            horizontal_results = await self.horizontal_checker.check_all(
                normalized['statements'],
                filing_id,
                taxonomy_accessor=taxonomy_accessor
            )
            
            self.logger.info(
                f"Horizontal checks: {horizontal_results['summary']['passed']}/"
                f"{horizontal_results['summary']['total']} passed"
            )
            
            anomaly_results = await self.anomaly_detector.detect_all(
                normalized['statements'],
                filing_id,
                taxonomy_accessor=taxonomy_accessor
            )
            
            self.logger.info(
                f"Anomalies detected: {len(anomaly_results['anomalies'])}"
            )
            
            # Calculate confidence score
            all_results = {
                'vertical': vertical_results,
                'horizontal': horizontal_results,
                'anomalies': anomaly_results,
                'normalization': normalized['metadata']
            }
            
            score_data = self.score_calculator.calculate_score(all_results)
            
            self.logger.info(
                f"Confidence score: {score_data['confidence_score']:.2f} "
                f"({score_data['category']})"
            )
            
            # Generate report
            processing_time = time.time() - start_time
            
            report = self.report_generator.generate_report(
                filing_id=filing_id,
                statements_metadata=metadata,
                score_data=score_data,
                all_results=all_results,
                processing_time=processing_time
            )
            
            # Save results
            report_path = self.validation_persister.save_results(
                filing_id=filing_id,
                report=report,
                normalized_statements=normalized['statements'],
                filing_metadata=parsed_metadata,
                other_data=other_data
            )
            
            self.logger.info(
                f"=== CCQ Validation Complete: {filing_id} "
                f"(Score: {score_data['confidence_score']:.2f}, "
                f"Time: {processing_time:.2f}s) ==="
            )
            
            return {
                'success': True,
                'filing_id': filing_id,
                'confidence_score': score_data['confidence_score'],
                'category': score_data['category'],
                'ready_for_analysis': score_data['ready_for_analysis'],
                'processing_time': processing_time,
                'report_path': report_path,
                'summary': {
                    'vertical_checks': vertical_results['summary'],
                    'horizontal_checks': horizontal_results['summary'],
                    'anomalies': anomaly_results['summary']
                }
            }
            
        except Exception as e:
            self.logger.error(
                f"CCQ validation failed for {filing_id}: {e}",
                exc_info=True
            )
            
            return {
                'success': False,
                'filing_id': filing_id,
                'error': str(e),
                'processing_time': time.time() - start_time
            }