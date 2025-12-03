# File: core/filing_metadata_parser.py
# Path: core/filing_metadata_parser.py

"""
Filing Metadata Parser
======================

Parses filing metadata from directory paths.

Handles standard path structures:
- /path/to/mapped_statements/market/entity/filing_type/filing_date/
- /path/to/entities/market/entity/filings/filing_type/accession/

Robust to different path variations and provides clear error messages.
"""

from pathlib import Path
from typing import Dict, Optional
from core.system_logger import get_logger

logger = get_logger(__name__)


class FilingMetadataParser:
    """
    Parses filing metadata from directory paths.
    
    Extracts: market, entity_name, filing_type, filing_date
    """
    
    # Known directory structure markers
    STRUCTURE_MARKERS = [
        'mapped_statements',
        'entities',
        'xbrl',
        'filings'
    ]
    
    @staticmethod
    def parse_from_path(filing_path: Path) -> Dict[str, str]:
        """
        Parse filing metadata from directory path.
        
        Args:
            filing_path: Path to filing directory
            
        Returns:
            Dict with keys: market, entity_name, filing_type, filing_date
            
        Raises:
            ValueError: If path structure cannot be parsed
            
        Examples:
            /data/mapped_statements/sec/APPLE_INC/10-K/2024-01-15
            -> {
                'market': 'sec',
                'entity_name': 'APPLE_INC',
                'filing_type': '10-K',
                'filing_date': '2024-01-15'
            }
        """
        path_parts = filing_path.parts
        
        # Try each known structure
        for marker in FilingMetadataParser.STRUCTURE_MARKERS:
            try:
                if marker in path_parts:
                    return FilingMetadataParser._parse_standard_structure(
                        path_parts, marker
                    )
            except (ValueError, IndexError):
                continue
        
        # If no known structure found, raise error
        raise ValueError(
            f"Cannot parse filing metadata from path: {filing_path}. "
            f"Expected structure with one of: {FilingMetadataParser.STRUCTURE_MARKERS}"
        )
    
    @staticmethod
    def _parse_standard_structure(
        path_parts: tuple,
        marker: str
    ) -> Dict[str, str]:
        """
        Parse standard structure: marker/market/entity/filing_type/filing_date
        
        Args:
            path_parts: Path components as tuple
            marker: Structure marker ('mapped_statements', 'entities', etc.)
            
        Returns:
            Parsed metadata dict
            
        Raises:
            ValueError: If structure doesn't match expected pattern
        """
        marker_idx = path_parts.index(marker)
        
        # Standard structure: marker/market/entity/type/date
        try:
            market = path_parts[marker_idx + 1]
            entity_name = path_parts[marker_idx + 2]
            
            # Handle 'filings' subdirectory in entities structure
            if marker == 'entities' and path_parts[marker_idx + 3] == 'filings':
                filing_type = path_parts[marker_idx + 4]
                filing_date = path_parts[marker_idx + 5]
            else:
                filing_type = path_parts[marker_idx + 3]
                filing_date = path_parts[marker_idx + 4]
            
            return {
                'market': market,
                'entity_name': entity_name,
                'filing_type': filing_type,
                'filing_date': filing_date
            }
        except IndexError as e:
            raise ValueError(
                f"Insufficient path components after '{marker}': {path_parts}"
            ) from e
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, str]) -> bool:
        """
        Validate that all required metadata fields are present and non-empty.
        
        Args:
            metadata: Metadata dict to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ['market', 'entity_name', 'filing_type', 'filing_date']
        
        missing = [
            field for field in required_fields
            if not metadata.get(field)
        ]
        
        if missing:
            raise ValueError(
                f"Missing required metadata fields: {missing}. "
                f"Got: {metadata}"
            )
        
        return True
    
    @staticmethod
    def merge_metadata(
        parsed: Dict[str, str],
        report: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Merge parsed metadata with report metadata.
        
        Prioritizes parsed metadata (from path) over report metadata.
        
        Args:
            parsed: Metadata parsed from path
            report: Metadata from report
            
        Returns:
            Merged metadata dict
        """
        return {
            'market': parsed.get('market') or report.get('market', 'unknown'),
            'entity_name': parsed.get('entity_name') or report.get('company_name', 'unknown'),
            'filing_type': parsed.get('filing_type') or report.get('filing_type', 'unknown'),
            'filing_date': parsed.get('filing_date') or report.get('filing_date', 'unknown')
        }


__all__ = ['FilingMetadataParser']