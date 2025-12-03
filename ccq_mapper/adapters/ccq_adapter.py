"""
CCQ Adapter
===========

Reads CCQ's native JSON format and translates to neutral format.

Location: engines/ccq_mapper/adapters/ccq_adapter.py

CCQ Format:
{
    "line_items": [
        {
            "qname": "us-gaap:Assets",
            "label": "Assets",
            "value": "1000000",
            "unit": "USD",
            "decimals": "-5",
            "context_ref": "As_Of_12_31_2024_...",
            "properties": {
                "balance_type": "debit",
                "period_type": "instant",
                "is_abstract": false,
                "is_nil": false
            },
            "classification": {
                "statement": "balance_sheet",
                "monetary_type": "monetary",
                "temporal_type": "instant",
                "accounting_type": "debit",
                "aggregation_level": "line_item"
            }
        }
    ]
}
"""

from typing import Dict, Any, List
from pathlib import Path
import json

from .neutral_format import (
    NeutralFact,
    normalize_concept_id,
    extract_namespace,
    extract_local_name,
    extract_date_from_context_id,
    validate_neutral_fact
)


class CCQAdapter:
    """
    Adapter for reading CCQ statement JSON files.
    
    Responsibilities:
    - Parse CCQ JSON structure
    - Extract items from 'line_items' array
    - Read 'qname' field (not 'concept')
    - Handle clean namespaces (us-gaap, no year)
    - Extract nested properties and classification
    - Preserve all original data in original_format
    - Translate to neutral format
    
    Does NOT:
    - Modify values
    - Filter concepts
    - Add concepts
    - Make judgments about correctness
    """
    
    VERSION = "1.0.0"
    
    def __init__(self):
        """Initialize CCQ adapter."""
        self.adapter_version = self.VERSION
        self.items_processed = 0
        self.errors = []
    
    def parse_statement_file(self, file_path: Path) -> List[NeutralFact]:
        """
        Parse a CCQ statement JSON file.
        
        Args:
            file_path: Path to CCQ JSON file
            
        Returns:
            List of NeutralFact objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"CCQ file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self.parse_statement(data)
    
    def parse_statement(self, data: Dict[str, Any]) -> List[NeutralFact]:
        """
        Parse CCQ statement data.
        
        Args:
            data: Parsed JSON data from CCQ
            
        Returns:
            List of NeutralFact objects
        """
        self.items_processed = 0
        self.errors = []
        
        # CCQ uses 'line_items' array
        line_items = data.get('line_items', [])
        
        neutral_facts = []
        for item_dict in line_items:
            try:
                neutral_fact = self.parse_item(item_dict)
                neutral_facts.append(neutral_fact)
                self.items_processed += 1
            except Exception as e:
                self.errors.append({
                    'item': item_dict,
                    'error': str(e)
                })
        
        return neutral_facts
    
    def parse_item(self, item_dict: Dict[str, Any]) -> NeutralFact:
        """
        Parse a single CCQ line item into neutral format.
        
        Args:
            item_dict: CCQ line item dictionary
            
        Returns:
            NeutralFact object
            
        Raises:
            ValueError: If required fields are missing
        """
        # Extract qname (CCQ uses 'qname' field, not 'concept')
        raw_qname = item_dict.get('qname')
        if not raw_qname:
            raise ValueError("Missing 'qname' field in CCQ item")
        
        # CCQ already uses clean namespaces (no year suffix)
        concept_id = raw_qname
        concept_namespace = extract_namespace(concept_id)
        concept_local_name = extract_local_name(concept_id)
        
        # Extract label
        label = item_dict.get('label', concept_local_name)
        
        # Extract value (preserve as string)
        value = str(item_dict.get('value', ''))
        
        # Extract unit
        unit = item_dict.get('unit')
        
        # Extract decimals
        decimals = item_dict.get('decimals')
        
        # Extract properties (nested dict)
        properties = item_dict.get('properties', {})
        period_type = properties.get('period_type')
        balance_type = properties.get('balance_type')
        is_abstract = properties.get('is_abstract', False)
        
        # Extract classification (nested dict)
        classification = item_dict.get('classification', {})
        statement_type = classification.get('statement')
        monetary_type = classification.get('monetary_type')
        temporal_type = classification.get('temporal_type')
        
        # Use temporal_type as fallback for period_type
        if not period_type and temporal_type:
            period_type = temporal_type
        
        # Extract context
        context_id = item_dict.get('context_ref', '')
        context_date = extract_date_from_context_id(context_id)
        
        # Determine if monetary
        is_monetary = self._is_monetary_item(item_dict, monetary_type)
        
        # Create neutral fact
        neutral_fact = NeutralFact(
            # Identity
            concept_id=concept_id,
            concept_namespace=concept_namespace,
            concept_local_name=concept_local_name,
            
            # Display
            label=label,
            
            # Value
            value=value,
            unit=unit,
            decimals=decimals,
            
            # Classification
            period_type=period_type,
            balance_type=balance_type,
            is_abstract=is_abstract,
            is_monetary=is_monetary,
            
            # Context
            context_id=context_id,
            context_date=context_date,
            
            # Provenance
            source_system='ccq',
            original_format=item_dict.copy(),  # CRITICAL: preserve original
            adapter_version=self.adapter_version,
            
            # Additional CCQ metadata
            statement_type=statement_type
        )
        
        # Validate
        is_valid, errors = validate_neutral_fact(neutral_fact)
        if not is_valid:
            raise ValueError(f"Invalid neutral fact: {errors}")
        
        return neutral_fact
    
    def _is_monetary_item(
        self,
        item_dict: Dict[str, Any],
        monetary_type: str
    ) -> bool:
        """
        Determine if item represents a monetary value.
        
        Args:
            item_dict: CCQ item dictionary
            monetary_type: Monetary type from classification
            
        Returns:
            True if monetary, False otherwise
        """
        # Check classification monetary_type
        if monetary_type in ['monetary', 'currency']:
            return True
        
        # Check unit (handle None case for TextBlocks and non-monetary facts)
        unit = item_dict.get('unit')
        if unit:
            unit_lower = unit.lower()
            if 'usd' in unit_lower or 'currency' in unit_lower:
                return True
        
        # No unit or non-monetary unit
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get adapter statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'adapter': 'CCQAdapter',
            'version': self.adapter_version,
            'items_processed': self.items_processed,
            'errors_count': len(self.errors),
            'errors': self.errors
        }


__all__ = ['CCQAdapter']