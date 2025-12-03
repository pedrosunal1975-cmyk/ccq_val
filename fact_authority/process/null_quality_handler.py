# File: engines/fact_authority/process/null_quality_handler.py
# Path: engines/fact_authority/process/null_quality_handler.py

"""
Null Quality Handler
===================

Handles null_quality.json from both Map Pro and CCQ mappers.

Responsibilities:
- Load null_quality files from both mappers
- Compare null quality patterns
- Identify common vs. unique null issues
- Generate null quality analysis report

Does NOT:
- Create a validated null_quality statement (only analysis)
- Make quality decisions (just analyzes)
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

from core.system_logger import get_logger
from core.data_paths import CCQPaths

logger = get_logger(__name__)


class NullQualityHandler:
    """
    Analyzes null quality data from both mappers.
    
    Compares null quality issues to understand:
    - Which facts have quality problems
    - Whether mappers agree on quality issues
    - Patterns in null quality data
    """
    
    def __init__(self, ccq_paths: CCQPaths):
        """
        Initialize handler with CCQPaths.
        
        Args:
            ccq_paths: CCQPaths instance for path resolution
        """
        self.logger = logger
        self.ccq_paths = ccq_paths
    
    def analyze_from_statements(
        self,
        map_pro_statements: Dict[str, Any],
        ccq_statements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze null quality from statement data.
        
        Extracts null quality information directly from statement
        metadata rather than loading separate null_quality.json files.
        
        Args:
            map_pro_statements: Map Pro statement data (with metadata)
            ccq_statements: CCQ statement data (with metadata)
            
        Returns:
            Null quality analysis dict
        """
        self.logger.info("Analyzing null quality from statements")
        
        # Extract null concepts from statement metadata
        map_pro_nulls = self._extract_nulls_from_statements(map_pro_statements)
        ccq_nulls = self._extract_nulls_from_statements(ccq_statements)
        
        # Extract concepts
        map_pro_concepts = self._extract_null_concepts(map_pro_nulls)
        ccq_concepts = self._extract_null_concepts(ccq_nulls)
        
        # Compare
        comparison = self._compare_null_quality(
            map_pro_concepts,
            ccq_concepts
        )
        
        # Analyze patterns
        patterns = self._analyze_null_patterns(
            map_pro_nulls,
            ccq_nulls
        )
        
        return {
            'null_quality_comparison': comparison,
            'map_pro_null_count': len(map_pro_concepts),
            'ccq_null_count': len(ccq_concepts),
            'common_null_concepts': sorted(list(comparison['common_nulls'])),
            'map_pro_only_nulls': sorted(list(comparison['map_pro_only'])),
            'ccq_only_nulls': sorted(list(comparison['ccq_only'])),
            'patterns': patterns
        }
    
    def analyze_null_quality(
        self,
        market: str,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> Dict[str, Any]:
        """
        Analyze null quality from separate null_quality.json files.
        
        Args:
            market: Market type
            entity_name: Entity name
            filing_type: Filing type
            filing_date: Filing date
            
        Returns:
            Null quality analysis dict
        """
        self.logger.info(
            f"Analyzing null quality for "
            f"{market}/{entity_name}/{filing_type}/{filing_date}"
        )
        
        # Build paths to null_quality.json files
        map_pro_dir = (
            self.ccq_paths.input_mapped /
            market /
            entity_name /
            filing_type /
            filing_date
        )
        
        ccq_dir = (
            self.ccq_paths.mapper_output /
            market /
            entity_name /
            filing_type /
            filing_date
        )
        
        # Load null quality files
        map_pro_nulls = self._load_null_quality(map_pro_dir / 'null_quality.json')
        ccq_nulls = self._load_null_quality(ccq_dir / 'null_quality.json')
        
        # Extract concepts
        map_pro_concepts = self._extract_null_concepts(map_pro_nulls)
        ccq_concepts = self._extract_null_concepts(ccq_nulls)
        
        # Compare
        comparison = self._compare_null_quality(
            map_pro_concepts,
            ccq_concepts
        )
        
        # Analyze patterns
        patterns = self._analyze_null_patterns(
            map_pro_nulls,
            ccq_nulls
        )
        
        return {
            'null_quality_comparison': comparison,
            'map_pro_null_count': len(map_pro_concepts),
            'ccq_null_count': len(ccq_concepts),
            'common_null_concepts': sorted(list(comparison['common_nulls'])),
            'map_pro_only_nulls': sorted(list(comparison['map_pro_only'])),
            'ccq_only_nulls': sorted(list(comparison['ccq_only'])),
            'patterns': patterns
        }
    
    def _extract_nulls_from_statements(
        self,
        statements: Dict[str, Any]
    ) -> List[Dict]:
        """
        Extract null quality facts from statement data.
        
        Args:
            statements: Statement data dict
            
        Returns:
            List of facts with null/quality issues
        """
        null_facts = []
        
        # Check metadata for null_quality info
        metadata = statements.get('metadata', {})
        if 'null_quality' in metadata:
            null_facts.extend(metadata['null_quality'])
        
        # Check each statement for null facts
        for stmt_type in ['balance_sheet', 'income_statement', 'cash_flow', 'other']:
            stmt_data = statements.get(stmt_type, {})
            stmt_metadata = stmt_data.get('metadata', {})
            
            if 'null_facts' in stmt_metadata:
                null_facts.extend(stmt_metadata['null_facts'])
        
        return null_facts
    
    def _load_null_quality(self, file_path: Path) -> List[Dict]:
        """
        Load null quality file.
        
        Returns empty list if file doesn't exist.
        
        Args:
            file_path: Path to null_quality.json
            
        Returns:
            List of null quality facts
        """
        if not file_path.exists():
            self.logger.debug(f"Null quality file not found: {file_path}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different formats
            if isinstance(data, dict):
                # Map Pro format: {'facts': [...]}
                return data.get('facts', data.get('line_items', []))
            elif isinstance(data, list):
                # Direct list format
                return data
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Failed to load null quality from {file_path}: {e}")
            return []
    
    def _extract_null_concepts(self, null_facts: List[Dict]) -> Set[str]:
        """
        Extract set of concepts with null/quality issues.
        
        Args:
            null_facts: List of facts with null issues
            
        Returns:
            Set of concept qnames
        """
        concepts = set()
        
        for fact in null_facts:
            concept = fact.get('concept_qname') or fact.get('qname')
            if concept:
                concepts.add(concept)
        
        return concepts
    
    def _compare_null_quality(
        self,
        map_pro_concepts: Set[str],
        ccq_concepts: Set[str]
    ) -> Dict[str, Any]:
        """
        Compare null quality between mappers.
        
        Returns analysis of agreement/disagreement.
        
        Args:
            map_pro_concepts: Concepts with null issues in Map Pro
            ccq_concepts: Concepts with null issues in CCQ
            
        Returns:
            Comparison analysis dict
        """
        common_nulls = map_pro_concepts & ccq_concepts
        map_pro_only = map_pro_concepts - ccq_concepts
        ccq_only = ccq_concepts - map_pro_concepts
        
        total_unique = len(map_pro_concepts | ccq_concepts)
        
        agreement_rate = 0.0
        if total_unique > 0:
            agreement_rate = (len(common_nulls) / total_unique) * 100
        
        return {
            'common_nulls': list(common_nulls),
            'map_pro_only': list(map_pro_only),
            'ccq_only': list(ccq_only),
            'agreement_rate': round(agreement_rate, 1),
            'summary': f"{len(common_nulls)} common, "
                      f"{len(map_pro_only)} Map Pro only, "
                      f"{len(ccq_only)} CCQ only"
        }
    
    def _analyze_null_patterns(
        self,
        map_pro_nulls: List[Dict],
        ccq_nulls: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze patterns in null quality data.
        
        Identifies common reasons for null quality.
        
        Args:
            map_pro_nulls: Map Pro null facts
            ccq_nulls: CCQ null facts
            
        Returns:
            Pattern analysis dict
        """
        patterns = {
            'map_pro_reasons': self._count_null_reasons(map_pro_nulls),
            'ccq_reasons': self._count_null_reasons(ccq_nulls),
            'total_map_pro': len(map_pro_nulls),
            'total_ccq': len(ccq_nulls)
        }
        
        return patterns
    
    def _count_null_reasons(self, null_facts: List[Dict]) -> Dict[str, int]:
        """
        Count reasons for null quality issues.
        
        Args:
            null_facts: List of facts with null issues
            
        Returns:
            Dict mapping reason to count
        """
        reasons = {}
        
        for fact in null_facts:
            # Extract reason (different mappers may use different keys)
            reason = (
                fact.get('null_reason') or
                fact.get('reason') or
                fact.get('quality_issue') or
                'unknown'
            )
            
            reasons[reason] = reasons.get(reason, 0) + 1
        
        return reasons


__all__ = ['NullQualityHandler']