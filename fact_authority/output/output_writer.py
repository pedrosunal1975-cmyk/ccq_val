# File: engines/fact_authority/output/output_writer.py
# Path: engines/fact_authority/output/output_writer.py

"""
Output Writer
=============

Writes fact_authority outputs to disk.

Responsibilities:
- Create output directory structure
- Write validated statement files
- Write reconciliation report
- Write null quality analysis
- Preserve company/market/form_type/date hierarchy
- Handle file naming conventions

Does NOT:
- Build statements (reconciler does that)
- Make decisions (reconciler does that)
- Generate reports (reporter does that)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from core.system_logger import get_logger
from core.data_paths import CCQPaths

logger = get_logger(__name__)


class OutputWriter:
    """
    Writes fact_authority outputs to unified_mapped directory.
    
    Creates directory structure and writes JSON files.
    Uses CCQPaths for all path resolution - NO hardcoded paths.
    """
    
    def __init__(self, ccq_paths: CCQPaths):
        """
        Initialize writer with CCQPaths.
        
        Args:
            ccq_paths: CCQPaths instance for path resolution
        """
        self.logger = logger
        self.ccq_paths = ccq_paths
        
        # Get unified output path
        if ccq_paths.unified_mapped is None:
            raise ValueError("Unified output path not configured in CCQPaths")
        
        self.base_path = ccq_paths.unified_mapped
        
        # Ensure base directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"OutputWriter initialized: {self.base_path}")
    
    def write_validated_statements(
        self,
        reconciliation_result: Dict[str, Any],
        reconciliation_report: Dict[str, Any],
        null_quality_analysis: Optional[Dict[str, Any]],
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Path:
        """
        Write all validated outputs for a filing.
        
        Args:
            reconciliation_result: Results from StatementReconciler
            reconciliation_report: Report from ReconciliationReporter
            null_quality_analysis: Analysis from NullQualityHandler (optional)
            market: Market identifier (sec, fca, esma)
            entity_name: Entity name
            filing_type: Form type (10-K, 10-Q, etc.)
            filing_date: Filing date (YYYY-MM-DD)
            
        Returns:
            Path to output directory
        """
        self.logger.info(
            f"Writing validated statements: "
            f"{market}/{entity_name}/{filing_type}/{filing_date}"
        )
        
        # Create output directory
        output_dir = self._create_output_directory(
            market,
            entity_name,
            filing_type,
            filing_date
        )
        
        # Write statement files
        statements = reconciliation_result.get('statements', {})
        for stmt_type, stmt_data in statements.items():
            if stmt_type == 'metadata':
                continue  # Skip overall metadata
            
            self._write_statement_file(
                output_dir,
                stmt_type,
                stmt_data
            )
        
        # Write reconciliation report
        self._write_reconciliation_report(
            output_dir,
            reconciliation_report
        )
        
        # Write null quality analysis (if provided)
        if null_quality_analysis:
            self._write_null_quality_analysis(
                output_dir,
                null_quality_analysis
            )
        
        self.logger.info(
            f"Wrote validated statements to {output_dir}"
        )
        
        return output_dir
    
    def _create_output_directory(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Path:
        """
        Create output directory with proper hierarchy.
        
        Structure: unified_mapped/market/entity/filing_type/filing_date/
        
        Args:
            market: Market identifier
            entity_name: Entity name
            filing_type: Filing type
            filing_date: Filing date
            
        Returns:
            Path to output directory
        """
        output_dir = (
            self.base_path /
            market.lower() /
            entity_name /
            filing_type /
            filing_date
        )
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.debug(f"Created output directory: {output_dir}")
        
        return output_dir
    
    def _write_statement_file(
        self,
        output_dir: Path,
        statement_type: str,
        statement_data: Dict[str, Any]
    ) -> Path:
        """
        Write a validated statement file.
        
        File naming: {statement_type}.json
        
        Args:
            output_dir: Output directory
            statement_type: Statement type
            statement_data: Statement data (with validated_facts)
            
        Returns:
            Path to written file
        """
        file_name = f"{statement_type}.json"
        file_path = output_dir / file_name
        
        try:
            # Structure output
            output_data = {
                'validated_facts': statement_data.get('validated_facts', []),
                'statistics': statement_data.get('statistics', {}),
                'metadata': {
                    'statement_type': statement_type,
                    'validation_engine': 'fact_authority',
                    'source': 'taxonomy_validated'
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            facts_count = len(output_data['validated_facts'])
            self.logger.debug(
                f"Wrote {statement_type}: {facts_count} facts -> {file_path}"
            )
            
            return file_path
            
        except Exception as e:
            self.logger.error(
                f"Failed to write {statement_type} to {file_path}: {e}"
            )
            raise
    
    def _write_reconciliation_report(
        self,
        output_dir: Path,
        report_data: Dict[str, Any]
    ) -> Path:
        """
        Write reconciliation report.
        
        File naming: reconciliation_report.json
        
        Args:
            output_dir: Output directory
            report_data: Report data
            
        Returns:
            Path to written file
        """
        file_path = output_dir / 'reconciliation_report.json'
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Wrote reconciliation report -> {file_path}")
            
            return file_path
            
        except Exception as e:
            self.logger.error(
                f"Failed to write reconciliation report to {file_path}: {e}"
            )
            raise
    
    def _write_null_quality_analysis(
        self,
        output_dir: Path,
        analysis_data: Dict[str, Any]
    ) -> Path:
        """
        Write null quality analysis.
        
        File naming: null_quality_analysis.json
        
        Args:
            output_dir: Output directory
            analysis_data: Null quality analysis data
            
        Returns:
            Path to written file
        """
        file_path = output_dir / 'null_quality_analysis.json'
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Wrote null quality analysis -> {file_path}")
            
            return file_path
            
        except Exception as e:
            self.logger.error(
                f"Failed to write null quality analysis to {file_path}: {e}"
            )
            raise


__all__ = ['OutputWriter']