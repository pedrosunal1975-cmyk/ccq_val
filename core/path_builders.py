# File: core/path_builders.py
# Path: core/path_builders.py

"""
Path Builders
=============

Constructs standardized paths for CCQ system components.

Responsibilities:
- Build input paths (Map Pro outputs, parsed facts, XBRL)
- Build output paths (CCQ validator, CCQ mapper, unified)
- Build taxonomy paths
- Ensure directory creation where needed
"""

from pathlib import Path
from typing import Optional


class PathBuilders:
    """
    Builds standardized paths for CCQ system.
    
    All path construction logic centralized here.
    """
    
    def __init__(self, base_paths: dict):
        """
        Initialize path builders.
        
        Args:
            base_paths: Dict containing base directory paths:
                - input_mapped: Map Pro mapped statements
                - output_validated: CCQ Validator output
                - parsed_facts: Map Pro parsed facts
                - taxonomies: Taxonomy libraries
                - mapper_xbrl: Raw XBRL filings (optional)
                - mapper_output: CCQ Mapper output (optional)
                - unified_mapped: Unified mapper output (optional)
        """
        self.input_mapped = base_paths.get('input_mapped')
        self.output_validated = base_paths.get('output_validated')
        self.parsed_facts = base_paths.get('parsed_facts')
        self.taxonomies = base_paths.get('taxonomies')
        self.mapper_xbrl = base_paths.get('mapper_xbrl')
        self.mapper_output = base_paths.get('mapper_output')
        self.unified_mapped = base_paths.get('unified_mapped')
    
    # ========================================================================
    # INPUT PATHS (Read-only sources)
    # ========================================================================
    
    def get_parsed_facts_path(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Path:
        """
        Get path to parsed facts directory.
        
        Structure: parsed_facts/market/entity/filing_type/filing_date/
        """
        return (
            self.parsed_facts /
            market /
            entity_name /
            filing_type /
            filing_date
        )
    
    def get_xbrl_filing_path(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str,
        filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        Get path to raw XBRL filing.
        
        Structure: mapper_xbrl/market/entity/filing_type/filing_date/
        
        Returns:
            Path to XBRL file/directory, or None if mapper_xbrl not configured
        """
        if not self.mapper_xbrl:
            return None
        
        xbrl_dir = (
            self.mapper_xbrl /
            market /
            entity_name /
            filing_type /
            filing_date
        )
        
        if filename:
            return xbrl_dir / filename
        return xbrl_dir
    
    # ========================================================================
    # CCQ VALIDATOR OUTPUT PATHS
    # ========================================================================
    
    def get_output_directory(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Path:
        """
        Get CCQ Validator output directory (mirrors Map Pro structure).
        
        Creates directory if it doesn't exist.
        
        Structure: output_validated/market/entity/filing_type/filing_date/
        """
        output_dir = (
            self.output_validated /
            market_type /
            entity_name /
            filing_type /
            filing_date
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def get_normalized_statement_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str,
        statement_type: str
    ) -> Path:
        """
        Get path for normalized statement output.
        
        Args:
            statement_type: 'income_statement', 'balance_sheet', 'cash_flow', 'other'
        
        Returns:
            Path to normalized statement file
        """
        output_dir = self.get_output_directory(
            market_type, entity_name, filing_type, filing_date
        )
        
        # Special handling for 'other' - no '_normalized' suffix
        if statement_type == 'other':
            return output_dir / 'other.json'
        else:
            return output_dir / f'{statement_type}_normalized.json'
    
    def get_validation_report_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Path:
        """Get path for CCQ validation report."""
        output_dir = self.get_output_directory(
            market_type, entity_name, filing_type, filing_date
        )
        return output_dir / 'ccq_validation_report.json'
    
    # ========================================================================
    # CCQ MAPPER OUTPUT PATHS
    # ========================================================================
    
    def get_mapper_output_directory(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """
        Get CCQ Mapper output directory.
        
        Creates directory if it doesn't exist.
        
        Structure: mapper_output/market/entity/filing_type/filing_date/
        
        Returns:
            Path or None if mapper_output not configured
        """
        if not self.mapper_output:
            return None
        
        output_dir = (
            self.mapper_output /
            market_type /
            entity_name /
            filing_type /
            filing_date
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def get_mapped_statement_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str,
        statement_type: str
    ) -> Optional[Path]:
        """
        Get path for CCQ Mapper mapped statement output.
        
        Args:
            statement_type: 'balance_sheet', 'income_statement', 'cash_flow', 'other'
        
        Returns:
            Path or None if not configured
        """
        output_dir = self.get_mapper_output_directory(
            market_type, entity_name, filing_type, filing_date
        )
        
        if not output_dir:
            return None
        
        return output_dir / f'{statement_type}_mapped.json'
    
    def get_mapper_validation_report_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Get path for CCQ Mapper taxonomy validation report."""
        output_dir = self.get_mapper_output_directory(
            market_type, entity_name, filing_type, filing_date
        )
        
        if not output_dir:
            return None
        
        return output_dir / 'taxonomy_validation_report.json'
    
    def get_mapper_comparison_report_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Get path for CCQ Mapper vs Map Pro comparison report."""
        output_dir = self.get_mapper_output_directory(
            market_type, entity_name, filing_type, filing_date
        )
        
        if not output_dir:
            return None
        
        return output_dir / 'map_pro_comparison.json'
    
    def get_mapper_metadata_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Get path for CCQ Mapper metadata file."""
        output_dir = self.get_mapper_output_directory(
            market_type, entity_name, filing_type, filing_date
        )
        
        if not output_dir:
            return None
        
        return output_dir / 'mapper_metadata.json'
    
    def get_mapper_null_quality_path(
        self,
        market_type: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Optional[Path]:
        """Get path for CCQ Mapper null quality report."""
        output_dir = self.get_mapper_output_directory(
            market_type, entity_name, filing_type, filing_date
        )
        
        if not output_dir:
            return None
        
        return output_dir / 'null_quality.json'
    
    # ========================================================================
    # TAXONOMY PATHS
    # ========================================================================
    
    def get_taxonomy_paths_for_filing(
        self,
        market: str,
        taxonomy_name: Optional[str] = None,
        taxonomy_version: Optional[str] = None
    ) -> list[Path]:
        """
        Get list of taxonomy paths for a filing.
        
        Taxonomies are stored in a 'libraries' subdirectory.
        
        Args:
            market: Market type (sec, fca, esma)
            taxonomy_name: Specific taxonomy name (e.g., 'us-gaap')
            taxonomy_version: Specific taxonomy version (e.g., '2024')
        
        Returns:
            List of taxonomy directory paths
        """
        taxonomy_paths = []
        
        # Taxonomies are in libraries subdirectory
        libraries_dir = self.taxonomies / 'libraries'
        
        if not libraries_dir.exists():
            # Fallback: try without libraries subdirectory
            libraries_dir = self.taxonomies
        
        if not libraries_dir.exists():
            return taxonomy_paths
        
        if taxonomy_name and taxonomy_version:
            # Specific taxonomy requested
            specific_path = libraries_dir / f"{taxonomy_name}-{taxonomy_version}"
            if specific_path.exists():
                taxonomy_paths.append(specific_path)
        else:
            # Return all active taxonomies
            for taxonomy_dir in libraries_dir.iterdir():
                if taxonomy_dir.is_dir():
                    taxonomy_paths.append(taxonomy_dir)
        
        return taxonomy_paths


__all__ = ['PathBuilders']