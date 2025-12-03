"""
Comparison Engine
=================

Core comparison logic shared by all statement comparators.
Contains file finding, loading, normalization, and comparison utilities.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from core.system_logger import get_logger
from core.data_paths import CCQPaths

logger = get_logger(__name__)


class ComparisonEngine:
    """
    Core comparison engine with shared utilities.
    
    Provides file finding, loading, and basic comparison logic
    used by all specialized comparators.
    """
    
    def __init__(self, paths: CCQPaths):
        """Initialize with CCQPaths instance."""
        self.paths = paths
    
    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================
    
    def find_statement_file(
        self,
        base_path: Path,
        market: str,
        company: str,
        form_type: str,
        filing_date: str,
        filename: str
    ) -> Optional[Path]:
        """
        Find statement file using name variation strategies.
        
        Uses CCQPaths name variation logic for robust file location.
        """
        name_variations = self.paths._generate_name_variations(company)
        
        for company_variant in name_variations:
            file_path = base_path / market / company_variant / form_type / filing_date / filename
            
            if file_path.exists():
                logger.debug(f"Found statement: {file_path}")
                return file_path
        
        logger.warning(f"Statement file not found. Tried {len(name_variations)} company name variations")
        logger.debug(f"First 5 variations: {name_variations[:5]}")
        
        return None
    
    def load_statement(self, file_path: Path) -> Dict[str, Any]:
        """Load statement JSON file."""
        logger.debug(f"Loading: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # ========================================================================
    # LINE ITEM EXTRACTION
    # ========================================================================
    
    def extract_line_items(self, statement: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract line items from statement.
        
        Handles both Map Pro and CCQ statement structures.
        """
        # CCQ structure: statement['line_items']
        if 'line_items' in statement:
            return statement['line_items']
        
        # Map Pro structure: statement['facts']
        if 'facts' in statement:
            return statement['facts']
        
        # Alternative: direct list
        if isinstance(statement, list):
            return statement
        
        logger.warning("Could not find line items in statement structure")
        return []
    
    def normalize_line_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a line item to have consistent keys.
        
        Map Pro uses 'concept', CCQ uses 'qname'.
        Also normalizes taxonomy years (us-gaap-2024 -> us-gaap).
        """
        normalized = item.copy()
        
        # Ensure 'qname' exists
        if 'qname' not in normalized and 'concept' in normalized:
            normalized['qname'] = normalized['concept']
        
        # Ensure 'concept' exists
        if 'concept' not in normalized and 'qname' in normalized:
            normalized['concept'] = normalized['qname']
        
        # Normalize taxonomy year suffixes
        # us-gaap-2024:Assets -> us-gaap:Assets
        # dei-2024:EntityName -> dei:EntityName
        if 'qname' in normalized:
            normalized['qname'] = self._normalize_taxonomy_year(normalized['qname'])
        if 'concept' in normalized:
            normalized['concept'] = self._normalize_taxonomy_year(normalized['concept'])
        
        return normalized
    
    def _normalize_taxonomy_year(self, concept: str) -> str:
        """
        Normalize taxonomy year suffixes.
        
        Examples:
            us-gaap-2024:Assets -> us-gaap:Assets
            dei-2024:EntityName -> dei:EntityName
            plug:CustomConcept -> plug:CustomConcept (unchanged)
        
        Args:
            concept: Concept name with potential year suffix
            
        Returns:
            Normalized concept name without year suffix
        """
        if not concept or ':' not in concept:
            return concept
        
        # Pattern: taxonomy-YYYY:concept -> taxonomy:concept
        # Match: us-gaap-2024, dei-2023, srt-2024, etc.
        import re
        return re.sub(r'-\d{4}:', ':', concept)
    
    # ========================================================================
    # VALUE OPERATIONS
    # ========================================================================
    
    def normalize_value(self, value: Any) -> Any:
        """Normalize value for comparison."""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return value
        
        if isinstance(value, str):
            clean = value.replace(',', '').strip()
            
            try:
                return int(clean)
            except ValueError:
                pass
            
            try:
                return float(clean)
            except ValueError:
                return value
        
        return value
    
    def values_equal(self, val1: Any, val2: Any, tolerance: float = 0.01) -> bool:
        """Check if two values are equal (with tolerance for floats)."""
        if val1 is None and val2 is None:
            return True
        
        if val1 is None or val2 is None:
            return False
        
        try:
            num1 = float(val1)
            num2 = float(val2)
            
            if num1 == num2:
                return True
            
            if abs(num1 - num2) <= tolerance:
                return True
            
            if num1 != 0:
                relative_diff = abs((num2 - num1) / num1)
                return relative_diff <= tolerance / 100
            
            return False
            
        except (ValueError, TypeError):
            return str(val1) == str(val2)
    
    # ========================================================================
    # PERIOD TYPE FILTERING
    # ========================================================================
    
    def is_instant_item(self, item: Dict[str, Any]) -> bool:
        """Check if item is an instant (point-in-time) item."""
        # Check period_type field
        if 'period_type' in item:
            return item['period_type'] == 'instant'
        
        # Check properties
        if 'properties' in item:
            properties = item['properties']
            if 'period_type' in properties:
                return properties['period_type'] == 'instant'
        
        # Check classification
        if 'classification' in item:
            classification = item['classification']
            if 'temporal_type' in classification:
                return classification['temporal_type'] == 'instant'
        
        # Analyze context_ref
        context_ref = item.get('context_ref', '')
        if context_ref:
            context_lower = context_ref.lower()
            
            duration_indicators = ['_to_', 'duration', 'ytd', 'period', 'for_the']
            if any(indicator in context_lower for indicator in duration_indicators):
                return False
            
            instant_indicators = ['instant', 'asof', 'as_of']
            if any(indicator in context_lower for indicator in instant_indicators):
                return True
        
        # Default to False (exclude unknown)
        logger.warning(f"Could not determine period_type for '{item.get('qname', 'unknown')}', excluding")
        return False
    
    def is_duration_item(self, item: Dict[str, Any]) -> bool:
        """Check if item is a duration (period) item."""
        return not self.is_instant_item(item)
    
    # ========================================================================
    # METADATA EXTRACTION
    # ========================================================================
    
    def extract_statement_metadata(self, statement: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from statement."""
        metadata = statement.get('metadata', {})
        
        return {
            'filing_id': metadata.get('filing_id') or statement.get('filing_id'),
            'company': statement.get('company', {}).get('name'),
            'period': statement.get('period'),
            'fact_count': metadata.get('fact_count') or len(statement.get('line_items', statement.get('facts', [])))
        }


__all__ = ['ComparisonEngine']