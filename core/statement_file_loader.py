# File: core/statement_file_loader.py
# Path: core/statement_file_loader.py

"""
Statement File Loader
=====================

Loads financial statement JSON files from filing directories.

Handles:
- Multiple naming conventions (cash_flow.json vs cash_flow_statement.json)
- Metadata extraction
- Null quality data
- Other.json pass-through
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json

from core.system_logger import get_logger

logger = get_logger(__name__)


class StatementFileLoader:
    """
    Loads financial statement files from filing directories.
    
    Handles various file naming conventions and extracts metadata.
    """
    
    # Map of statement types to possible filenames
    STATEMENT_FILES = {
        'balance_sheet': ['balance_sheet.json'],
        'income_statement': ['income_statement.json'],
        'cash_flow': ['cash_flow.json', 'cash_flow_statement.json']
    }
    
    # Special files
    NULL_QUALITY_FILE = 'null_quality.json'
    OTHER_FILE = 'other.json'
    
    @staticmethod
    def load_statements_from_directory(
        filing_path: Path
    ) -> Dict[str, Any]:
        """
        Load all statement files from a filing directory.
        
        Args:
            filing_path: Path to filing directory containing JSON files
            
        Returns:
            Dict containing:
                - statements: Dict of statement_type -> statement_data
                - metadata: Extracted metadata from first statement
                - null_quality_data: Null quality assessment (if present)
                - other_data: Other.json data (if present)
                
        Raises:
            ValueError: If no statement files found
        """
        statements = {}
        metadata = {}
        null_quality_data = None
        other_data = None
        
        # Load main financial statements
        for stmt_type, filenames in StatementFileLoader.STATEMENT_FILES.items():
            stmt_data = StatementFileLoader._load_statement(
                filing_path, stmt_type, filenames
            )
            
            if stmt_data:
                statements[stmt_type] = stmt_data
                
                # Extract metadata from first statement found
                if 'metadata' in stmt_data and not metadata:
                    metadata = stmt_data['metadata']
        
        # Load null quality data
        null_quality_file = filing_path / StatementFileLoader.NULL_QUALITY_FILE
        if null_quality_file.exists():
            null_quality_data = StatementFileLoader._load_json_file(null_quality_file)
            logger.debug(f"Loaded {StatementFileLoader.NULL_QUALITY_FILE}")
        
        # Load other.json (pass-through, no normalization)
        other_file = filing_path / StatementFileLoader.OTHER_FILE
        if other_file.exists():
            other_data = StatementFileLoader._load_json_file(other_file)
            statements['other'] = other_data
            logger.debug(f"Loaded {StatementFileLoader.OTHER_FILE}")
        
        if not statements:
            raise ValueError(f"No statement files found in {filing_path}")
        
        logger.info(f"Loaded {len(statements)} statements: {list(statements.keys())}")
        
        # Add null quality to metadata if present
        if null_quality_data:
            metadata['null_quality'] = null_quality_data
        
        return {
            'statements': statements,
            'metadata': metadata,
            'null_quality_data': null_quality_data,
            'other_data': other_data
        }
    
    @staticmethod
    def _load_statement(
        filing_path: Path,
        stmt_type: str,
        filenames: list
    ) -> Optional[Dict[str, Any]]:
        """
        Load a statement file, trying multiple filename variants.
        
        Args:
            filing_path: Filing directory path
            stmt_type: Statement type (for logging)
            filenames: List of possible filenames to try
            
        Returns:
            Statement data dict or None if not found
        """
        for filename in filenames:
            stmt_file = filing_path / filename
            if stmt_file.exists():
                data = StatementFileLoader._load_json_file(stmt_file)
                logger.debug(f"Loaded {filename} as {stmt_type}")
                return data
        
        return None
    
    @staticmethod
    def _load_json_file(file_path: Path) -> Dict[str, Any]:
        """
        Load a JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If file cannot be parsed
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}") from e
        except Exception as e:
            raise ValueError(f"Cannot read {file_path}: {e}") from e
    
    @staticmethod
    def wrap_statements_with_metadata(
        statements: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Wrap statements with metadata for processing.
        
        Args:
            statements: Statement data dict
            metadata: Metadata dict
            
        Returns:
            Dict with 'metadata' key + statement keys
        """
        return {
            'metadata': metadata,
            **statements
        }


__all__ = ['StatementFileLoader']