# File: engines/ccq_mapper/orchestration/output_writer.py

"""
Output Writer
=============

Handles writing all mapper outputs to filesystem.

Responsibility:
- Write statement JSON files
- Write null_quality.json
- Write duplicates.json
- Write gaps.json
- Manage output directories
"""

from typing import Dict, Any, List
from pathlib import Path
import json

from core.system_logger import get_logger
from core.data_paths import CCQPaths

logger = get_logger(__name__)


class OutputWriter:
    """Writes all mapper outputs to filesystem."""
    
    def __init__(self, paths: CCQPaths):
        """
        Initialize output writer.
        
        Args:
            paths: CCQPaths instance for path resolution
        """
        self.paths = paths
        self.logger = logger
    
    def write_all_outputs(
        self,
        constructed_statements: List[Dict[str, Any]],
        null_quality_report: Dict[str, Any],
        duplicate_report: Dict[str, Any],
        gap_report: Dict[str, Any],
        filing_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Write ALL outputs: statements + null_quality.json + duplicates.json + gaps.json.
        
        Uses CCQPaths for proper path resolution - NO hardcoded paths.
        Follows existing filesystem naming conventions exactly.
        
        Args:
            constructed_statements: List of constructed statements
            null_quality_report: Null quality validation report
            duplicate_report: Duplicate analysis report
            gap_report: Gap analysis report
            filing_id: Filing identifier
            metadata: Filing metadata
            
        Returns:
            Dictionary mapping output types to file paths
        """
        self.logger.info(
            f"Writing {len(constructed_statements)} statements + "
            f"null_quality.json + duplicates.json + gaps.json"
        )
        
        # Extract path components from metadata
        market = metadata.get('market')
        if not market:
            raise ValueError("Market not specified in metadata")
        
        # Get company name from source_file path (maintains filesystem convention)
        source_file = metadata.get('source_file')
        if source_file:
            # Extract company name from actual filesystem path
            # e.g., /parsed_facts/sec/PLUG_POWER_INC/10-K/... -> PLUG_POWER_INC
            parts = Path(source_file).parts
            if market in parts:
                market_idx = parts.index(market)
                company_name = parts[market_idx + 1] if len(parts) > market_idx + 1 else None
            else:
                company_name = metadata.get('company', metadata.get('company_name'))
        else:
            company_name = metadata.get('company', metadata.get('company_name'))
        
        if not company_name:
            raise ValueError("Company name could not be determined")
        
        form_type = metadata.get('filing_type', metadata.get('form_type'))
        if not form_type:
            raise ValueError("Filing type not specified in metadata")
        
        filing_date = metadata.get('filing_date')
        if not filing_date:
            raise ValueError("Filing date not specified in metadata")
        
        # Get output directory using CCQPaths
        output_directory = self.paths.get_mapper_output_directory(
            market, company_name, form_type, filing_date
        )
        
        if not output_directory:
            raise ValueError("Mapper output path not configured in .env")
        
        self.logger.info(f"Output directory: {output_directory}")
        
        file_paths = {}
        
        # Write statement files
        for statement in constructed_statements:
            stmt_type = statement.get('statement_type', 'other')
            stmt_file = output_directory / f"{stmt_type}.json"
            
            try:
                with open(stmt_file, 'w', encoding='utf-8') as f:
                    json.dump(statement, f, indent=2, default=str)
                
                file_paths[stmt_type] = str(stmt_file)
                self.logger.info(f"[OK] Wrote {stmt_type}.json")
                
            except Exception as e:
                self.logger.error(f"Failed to write {stmt_type}: {e}")
        
        # Write null_quality.json
        null_quality_path = self.paths.get_mapper_null_quality_path(
            market, company_name, form_type, filing_date
        )
        
        if null_quality_path:
            try:
                with open(null_quality_path, 'w', encoding='utf-8') as f:
                    json.dump(null_quality_report, f, indent=2, default=str)
                
                file_paths['null_quality'] = str(null_quality_path)
                self.logger.info(f"[OK] Wrote null_quality.json")
                
            except Exception as e:
                self.logger.error(f"Failed to write null_quality.json: {e}")
        else:
            self.logger.warning("Null quality path could not be determined")
        
        # Write duplicates.json (same directory as statements)
        if duplicate_report:
            duplicates_path = output_directory / "duplicates.json"
            try:
                with open(duplicates_path, 'w', encoding='utf-8') as f:
                    json.dump(duplicate_report, f, indent=2, default=str)
                
                file_paths['duplicates'] = str(duplicates_path)
                self.logger.info(f"[OK] Wrote duplicates.json")
                
            except Exception as e:
                self.logger.error(f"Failed to write duplicates.json: {e}")
        
        # Write gaps.json (same directory as statements)
        if gap_report:
            gaps_path = output_directory / "gaps.json"
            try:
                with open(gaps_path, 'w', encoding='utf-8') as f:
                    json.dump(gap_report, f, indent=2, default=str)
                
                file_paths['gaps'] = str(gaps_path)
                self.logger.info(f"[OK] Wrote gaps.json")
                
            except Exception as e:
                self.logger.error(f"Failed to write gaps.json: {e}")
        
        self.logger.info(f"Successfully wrote {len(file_paths)} output files")
        
        return file_paths


__all__ = ['OutputWriter']