# File: engines/fact_authority/input/statement_loader.py
# Path: engines/fact_authority/input/statement_loader.py

"""
Statement Loader
================

Loads mapped statement outputs from Map Pro and CCQ mappers.

This is a simple loader that loads whatever statements exist in the
mapper output directories. Does NOT make judgments or validate.

Responsibilities:
    - Find statement files using CCQPaths
    - Load and parse JSON statement files
    - Handle different output formats (Map Pro vs CCQ)
    - Handle entity name variations between Map Pro and CCQ automatically
    - Normalize to consistent structure
    - Return statement data

Does NOT:
    - Make reconciliation decisions (reconciler does that)
    - Validate against taxonomy (reconciler does that)
    - Construct new statements (output_writer does that)
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.system_logger import get_logger
from core.data_paths import CCQPaths
from core.name_normalizer import NameNormalizer

logger = get_logger(__name__)


class StatementLoader:
    """
    Loads mapped statements from Map Pro and CCQ mappers.
    
    Handles both output formats and provides unified interface.
    Uses CCQPaths for all path resolution - NO hardcoded paths.
    
    Automatically handles entity name variations between Map Pro and CCQ
    using NameNormalizer (e.g., VISA_INC. vs VISA_INC_).
    """
    
    # Statement types to load
    STATEMENT_TYPES = [
        'balance_sheet',
        'income_statement',
        'cash_flow',
        'other'
    ]
    
    def __init__(self, ccq_paths: CCQPaths):
        """
        Initialize statement loader.
        
        Args:
            ccq_paths: CCQPaths instance for path resolution
        """
        self.logger = logger
        self.ccq_paths = ccq_paths
    
    def load_map_pro_statements(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Dict[str, Any]:
        """
        Load Map Pro statement files for a filing.
        
        Args:
            market: Market type ('sec', 'fca', 'esma')
            entity_name: Entity identifier (Map Pro's directory name)
            filing_type: Filing type ('10-K', '10-Q', etc.)
            filing_date: Filing date (YYYY-MM-DD)
            
        Returns:
            {
                'balance_sheet': {'facts': [...], 'metadata': {...}},
                'income_statement': {'facts': [...], 'metadata': {...}},
                'cash_flow': {'facts': [...], 'metadata': {...}},
                'other': {'facts': [...], 'metadata': {...}},
                'metadata': {
                    'source': 'map_pro',
                    'total_facts': N,
                    'statements_loaded': [...]
                }
            }
            
        Raises:
            FileNotFoundError: If statement directory doesn't exist
        """
        self.logger.info(
            f"Loading Map Pro statements: "
            f"{market}/{entity_name}/{filing_type}/{filing_date}"
        )
        
        # Build directory path using CCQPaths structure
        statements_dir = (
            self.ccq_paths.input_mapped /
            market /
            entity_name /
            filing_type /
            filing_date
        )
        
        if not statements_dir.exists():
            raise FileNotFoundError(
                f"Map Pro statements not found: {statements_dir}"
            )
        
        return self._load_statements_from_directory(
            statements_dir,
            source='map_pro',
            loader_func=self._load_map_pro_statement
        )
    
    def load_ccq_statements(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Dict[str, Any]:
        """
        Load CCQ statement files for a filing.
        
        Automatically searches for entity name variations if the standard
        path doesn't exist (e.g., VISA_INC. vs VISA_INC_).
        
        Args:
            market: Market type ('sec', 'fca', 'esma')
            entity_name: Entity identifier (Map Pro's directory name)
            filing_type: Filing type ('10-K', '10-Q', etc.')
            filing_date: Filing date (YYYY-MM-DD)
            
        Returns:
            Same format as load_map_pro_statements()
            
        Raises:
            FileNotFoundError: If statement directory doesn't exist
        """
        self.logger.info(
            f"Loading CCQ statements: "
            f"{market}/{entity_name}/{filing_type}/{filing_date}"
        )
        
        if self.ccq_paths.mapper_output is None:
            raise FileNotFoundError("CCQ mapper output path not configured")
        
        # Try standard path first
        statements_dir = (
            self.ccq_paths.mapper_output /
            market /
            entity_name /
            filing_type /
            filing_date
        )
        
        if statements_dir.exists():
            return self._load_statements_from_directory(
                statements_dir,
                source='ccq',
                loader_func=self._load_ccq_statement
            )
        
        # Standard path doesn't exist - try name variations
        self.logger.debug(
            f"CCQ statements not found at {statements_dir}, "
            f"trying name variations for '{entity_name}'"
        )
        
        # Generate name variations
        variations = NameNormalizer.generate_variations(entity_name)
        
        # Reconstruct market directory
        market_dir = self.ccq_paths.mapper_output / market
        
        for variation in variations:
            variant_dir = market_dir / variation / filing_type / filing_date
            
            if variant_dir.exists():
                self.logger.info(
                    f"Found CCQ statements using name variation: {variation}"
                )
                return self._load_statements_from_directory(
                    variant_dir,
                    source='ccq',
                    loader_func=self._load_ccq_statement
                )
        
        # Not found with any variation
        raise FileNotFoundError(
            f"CCQ statements not found: {statements_dir} "
            f"(tried {len(variations)} name variations)"
        )
    
    def _load_statements_from_directory(
        self,
        statements_dir: Path,
        source: str,
        loader_func: callable
    ) -> Dict[str, Any]:
        """
        Load all statement files from a directory.
        
        Args:
            statements_dir: Directory containing statement JSON files
            source: Source identifier ('map_pro' or 'ccq')
            loader_func: Function to load individual statement
            
        Returns:
            Dictionary with statements and metadata
        """
        statements = {}
        total_facts = 0
        
        for stmt_type in self.STATEMENT_TYPES:
            # Both Map Pro and CCQ use same filename format
            stmt_file = statements_dir / f"{stmt_type}.json"
            
            if not stmt_file.exists():
                self.logger.debug(
                    f"{source.upper()} {stmt_type} not found: {stmt_file}"
                )
                continue
            
            try:
                stmt_data = loader_func(stmt_file)
                statements[stmt_type] = stmt_data
                total_facts += len(stmt_data.get('facts', []))
                
            except Exception as e:
                self.logger.error(
                    f"Failed to load {source.upper()} {stmt_type}: {e}"
                )
                continue
        
        self.logger.info(
            f"Loaded {len(statements)} {source.upper()} statements "
            f"with {total_facts} total facts"
        )
        
        return {
            **statements,
            'metadata': {
                'source': source,
                'statements_loaded': list(statements.keys()),
                'total_facts': total_facts,
                'source_directory': str(statements_dir)
            }
        }
    
    def _load_map_pro_statement(self, file_path: Path) -> Dict[str, Any]:
        """
        Load and parse Map Pro statement file.
        
        Map Pro format:
        {
            'facts': [{fact_id, concept_qname, value, ...}, ...],
            'metadata': {...}
        }
        
        Args:
            file_path: Path to statement JSON file
            
        Returns:
            Dict with facts, metadata, source_file
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Map Pro uses 'facts' key
        facts = data.get('facts', [])
        metadata = data.get('metadata', {})
        
        return {
            'facts': facts,
            'metadata': metadata,
            'source_file': str(file_path)
        }
    
    def _load_ccq_statement(self, file_path: Path) -> Dict[str, Any]:
        """
        Load and parse CCQ statement file.
        
        CCQ format:
        {
            'line_items': [{qname, label, value, classification, ...}, ...],
            'statement_metadata': {...}
        }
        
        Args:
            file_path: Path to statement JSON file
            
        Returns:
            Dict with facts (normalized), metadata, source_file
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # CCQ uses 'line_items' key
        line_items = data.get('line_items', [])
        metadata = data.get('statement_metadata', {})
        
        # Normalize to 'facts' for consistency
        facts = self._normalize_ccq_facts(line_items)
        
        return {
            'facts': facts,
            'metadata': metadata,
            'source_file': str(file_path)
        }
    
    def _normalize_ccq_facts(self, line_items: List[Dict]) -> List[Dict]:
        """
        Normalize CCQ line_items to common fact format.
        
        Ensures both Map Pro and CCQ facts have consistent structure
        for comparison.
        
        Args:
            line_items: CCQ line_items from statement file
            
        Returns:
            List of normalized fact dicts
        """
        normalized = []
        
        for item in line_items:
            # Extract concept (CCQ uses 'qname' field)
            concept = item.get('qname') or item.get('concept_qname')
            
            if not concept:
                # Skip items without concept
                continue
            
            # Normalize to consistent format
            normalized_fact = {
                'concept_qname': concept,
                'value': item.get('value'),
                'label': item.get('label'),
                'context_ref': item.get('context_ref'),
                'unit': item.get('unit'),
                'decimals': item.get('decimals'),
                'classification': item.get('classification', {}),
                'properties': item.get('properties', {}),
                'source': 'ccq'
            }
            
            normalized.append(normalized_fact)
        
        return normalized


__all__ = ['StatementLoader']