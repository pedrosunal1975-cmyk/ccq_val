# File: core/validation_persister.py
# Path: core/validation_persister.py

"""
Validation Persister
====================

Saves validation results to files and database.

Responsibilities:
- Write validation reports
- Write normalized statements
- Copy pass-through files (other.json)
- Save to database (insert or update)
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json

from core.system_logger import get_logger
from core import data_paths

logger = get_logger(__name__)


class ValidationPersister:
    """
    Persists validation results to filesystem and database.
    
    Handles both file writing and database operations.
    """
    
    def __init__(
        self,
        report_generator,
        db_coordinator: Optional[Any] = None
    ):
        """
        Initialize validation persister.
        
        Args:
            report_generator: ReportGenerator instance for writing reports
            db_coordinator: Optional database coordinator
        """
        self.report_generator = report_generator
        self.db_coordinator = db_coordinator
        self.logger = logger
    
    def save_results(
        self,
        filing_id: str,
        report: Dict[str, Any],
        normalized_statements: Dict[str, Any],
        filing_metadata: Dict[str, str],
        other_data: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save validation results to files and database.
        
        Args:
            filing_id: Filing identifier
            report: Validation report
            normalized_statements: Normalized statement data
            filing_metadata: Filing metadata (market, entity_name, filing_type, filing_date)
            other_data: Optional other.json data to copy through
            
        Returns:
            Path to saved validation report
            
        Raises:
            ValueError: If required metadata is missing
            RuntimeError: If file writing fails
        """
        # Validate metadata
        self._validate_metadata(filing_metadata)
        
        # Save validation report
        report_path = self._save_report(report, filing_metadata)
        
        # Save normalized statements
        self._save_statements(normalized_statements, filing_metadata)
        
        # Copy other.json if present
        if other_data:
            self._save_other_data(other_data, filing_metadata)
        
        # Save to database if available
        if self.db_coordinator:
            self._save_to_database(filing_id, report, filing_metadata)
        
        return report_path
    
    def _validate_metadata(self, metadata: Dict[str, str]) -> None:
        """
        Validate required filing metadata is present.
        
        Args:
            metadata: Filing metadata dict
            
        Raises:
            ValueError: If required fields are missing
        """
        required = ['market', 'entity_name', 'filing_type', 'filing_date']
        missing = [k for k in required if not metadata.get(k)]
        
        if missing:
            raise ValueError(
                f"Missing required metadata: {missing}. Got: {metadata}"
            )
    
    def _save_report(
        self,
        report: Dict[str, Any],
        filing_metadata: Dict[str, str]
    ) -> Path:
        """
        Save validation report to file.
        
        Args:
            report: Validation report
            filing_metadata: Filing metadata
            
        Returns:
            Path to saved report
        """
        report_path = self.report_generator.write_report(
            report=report,
            filing_metadata=filing_metadata
        )
        
        self.logger.info(f"Report saved to: {report_path}")
        return report_path
    
    def _save_statements(
        self,
        normalized_statements: Dict[str, Any],
        filing_metadata: Dict[str, str]
    ) -> None:
        """
        Save normalized statements to files.
        
        Args:
            normalized_statements: Statement data by type
            filing_metadata: Filing metadata
        """
        for stmt_type, stmt_data in normalized_statements.items():
            if stmt_data and stmt_type != 'metadata':
                stmt_path = data_paths.ccq_paths.get_normalized_statement_path(
                    market_type=filing_metadata['market'],
                    entity_name=filing_metadata['entity_name'],
                    filing_type=filing_metadata['filing_type'],
                    filing_date=filing_metadata['filing_date'],
                    statement_type=stmt_type
                )
                
                with open(stmt_path, 'w') as f:
                    json.dump(stmt_data, f, indent=2, default=str)
                
                self.logger.debug(f"Saved {stmt_type} to: {stmt_path}")
    
    def _save_other_data(
        self,
        other_data: Dict[str, Any],
        filing_metadata: Dict[str, str]
    ) -> None:
        """
        Copy other.json to output (no normalization).
        
        Args:
            other_data: Other.json data
            filing_metadata: Filing metadata
        """
        other_path = (
            data_paths.ccq_paths.get_output_directory(
                market_type=filing_metadata['market'],
                entity_name=filing_metadata['entity_name'],
                filing_type=filing_metadata['filing_type'],
                filing_date=filing_metadata['filing_date']
            ) / 'other.json'
        )
        
        with open(other_path, 'w') as f:
            json.dump(other_data, f, indent=2, default=str)
        
        self.logger.debug(f"Copied other.json to: {other_path}")
    
    def _save_to_database(
        self,
        filing_id: str,
        report: Dict[str, Any],
        filing_metadata: Dict[str, str]
    ) -> None:
        """
        Save validation results to database (INSERT or UPDATE).
        
        Args:
            filing_id: Filing identifier
            report: Validation report
            filing_metadata: Filing metadata
        """
        try:
            # Import here to avoid circular dependencies
            from database.models.ccq_models import ValidatedFiling
            
            with self.db_coordinator.get_session() as session:
                # Extract validation summary
                validation_summary = report.get('validation_summary', {})
                report_filing_metadata = report.get('filing_metadata', {})
                
                # Check if record exists
                existing = session.query(ValidatedFiling).filter_by(
                    filing_id=filing_id
                ).first()
                
                if existing:
                    # UPDATE existing record
                    self._update_database_record(
                        existing, filing_metadata, report_filing_metadata,
                        validation_summary, report
                    )
                    self.logger.debug(
                        f"Updated validation record in database for {filing_id}"
                    )
                else:
                    # INSERT new record
                    new_record = self._create_database_record(
                        filing_id, filing_metadata, report_filing_metadata,
                        validation_summary, report
                    )
                    session.add(new_record)
                    self.logger.debug(
                        f"Inserted validation record in database for {filing_id}"
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to save to database: {e}", exc_info=True)
            # Don't raise - database save is optional
    
    def _update_database_record(
        self,
        record,
        filing_metadata: Dict[str, str],
        report_metadata: Dict[str, str],
        validation_summary: Dict[str, Any],
        report: Dict[str, Any]
    ) -> None:
        """Update existing database record."""
        # Filing metadata
        record.company_name = filing_metadata['entity_name']
        record.filing_type = filing_metadata['filing_type']
        record.filing_date = filing_metadata['filing_date']
        record.market = filing_metadata['market']
        
        # Additional metadata from report
        record.cik = report_metadata.get('cik')
        record.fiscal_year = report_metadata.get('fiscal_year')
        record.fiscal_period = report_metadata.get('fiscal_period')
        
        # File paths
        record.input_directory = report_metadata.get('input_directory', '')
        record.output_directory = report_metadata.get('output_directory', '')
        record.validation_report_path = report_metadata.get('validation_report_path', '')
        
        # Validation results
        record.validation_status = 'completed'
        record.overall_pass = validation_summary.get('ready_for_analysis', False)
        record.confidence_score = validation_summary.get('confidence_score')
        record.ready_for_analysis = validation_summary.get('ready_for_analysis', False)
        
        # Statement-level status
        stmt_status = validation_summary.get('statement_status', {})
        record.income_statement_status = stmt_status.get('income_statement')
        record.balance_sheet_status = stmt_status.get('balance_sheet')
        record.cash_flow_status = stmt_status.get('cash_flow')
        
        # Statistics
        record.total_checks_performed = validation_summary.get('total_checks')
        record.checks_passed = validation_summary.get('checks_passed')
        record.checks_failed = validation_summary.get('checks_failed')
        record.checks_warning = validation_summary.get('checks_warning')
        
        # Anomalies
        record.critical_anomalies_count = validation_summary.get('critical_anomalies', 0)
        record.warning_anomalies_count = validation_summary.get('warning_anomalies', 0)
        record.info_anomalies_count = validation_summary.get('info_anomalies', 0)
        
        # Processing metadata
        record.processing_time_seconds = report.get('processing_time')
        record.updated_at = datetime.now(timezone.utc)
    
    def _create_database_record(
        self,
        filing_id: str,
        filing_metadata: Dict[str, str],
        report_metadata: Dict[str, str],
        validation_summary: Dict[str, Any],
        report: Dict[str, Any]
    ):
        """Create new database record."""
        from database.models.ccq_models import ValidatedFiling
        
        stmt_status = validation_summary.get('statement_status', {})
        
        return ValidatedFiling(
            filing_id=filing_id,
            company_name=filing_metadata['entity_name'],
            cik=report_metadata.get('cik'),
            filing_type=filing_metadata['filing_type'],
            filing_date=filing_metadata['filing_date'],
            fiscal_year=report_metadata.get('fiscal_year'),
            fiscal_period=report_metadata.get('fiscal_period'),
            market=filing_metadata['market'],
            
            # File paths
            input_directory=report_metadata.get('input_directory', ''),
            output_directory=report_metadata.get('output_directory', ''),
            validation_report_path=report_metadata.get('validation_report_path', ''),
            
            # Validation results
            validation_status='completed',
            overall_pass=validation_summary.get('ready_for_analysis', False),
            confidence_score=validation_summary.get('confidence_score'),
            ready_for_analysis=validation_summary.get('ready_for_analysis', False),
            
            # Statement-level status
            income_statement_status=stmt_status.get('income_statement'),
            balance_sheet_status=stmt_status.get('balance_sheet'),
            cash_flow_status=stmt_status.get('cash_flow'),
            
            # Statistics
            total_checks_performed=validation_summary.get('total_checks'),
            checks_passed=validation_summary.get('checks_passed'),
            checks_failed=validation_summary.get('checks_failed'),
            checks_warning=validation_summary.get('checks_warning'),
            
            # Anomalies
            critical_anomalies_count=validation_summary.get('critical_anomalies', 0),
            warning_anomalies_count=validation_summary.get('warning_anomalies', 0),
            info_anomalies_count=validation_summary.get('info_anomalies', 0),
            
            # Processing metadata
            processing_time_seconds=report.get('processing_time')
        )


__all__ = ['ValidationPersister']