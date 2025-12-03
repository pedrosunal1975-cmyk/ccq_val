# EXAMPLE: Modified map_pro_adapter.py with Taxonomy Lookup
# This shows the EXACT changes needed to fix period_type inference

"""
Map Pro Adapter (FIXED VERSION)
================================

Key Changes from Original:
1. Accept taxonomy_loader and taxonomy_data in __init__
2. Use taxonomy as PRIMARY source for period_type
3. Fall back to context inference only if taxonomy lookup fails
4. Preserve existing error handling and structure
"""

from typing import Dict, Any, List, Optional
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


class MapProAdapter:
    """
    Adapter for reading Map Pro statement JSON files.
    
    FIXED: Now uses taxonomy as primary source for period_type.
    """
    
    VERSION = "2.0.0"  # Incremented due to taxonomy integration
    
    def __init__(
        self, 
        taxonomy_loader=None, 
        taxonomy_data=None
    ):
        """
        Initialize Map Pro adapter.
        
        Args:
            taxonomy_loader: Optional TaxonomyLoader instance for concept lookup
            taxonomy_data: Optional preloaded taxonomy data (for performance)
        """
        self.adapter_version = self.VERSION
        self.facts_processed = 0
        self.errors = []
        
        # NEW: Taxonomy access for authoritative period_type
        self.taxonomy_loader = taxonomy_loader
        self.taxonomy_data = taxonomy_data
        
        # Statistics for debugging
        self.period_type_sources = {
            'taxonomy': 0,
            'context_inference': 0,
            'map_pro_metadata': 0
        }
    
    def parse_statement_file(self, file_path: Path) -> List[NeutralFact]:
        """Parse a Map Pro statement JSON file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Map Pro file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self.parse_statement(data)
    
    def parse_statement(self, data: Dict[str, Any]) -> List[NeutralFact]:
        """Parse Map Pro statement data."""
        self.facts_processed = 0
        self.errors = []
        
        facts_array = data.get('facts', [])
        
        neutral_facts = []
        for fact_dict in facts_array:
            try:
                neutral_fact = self.parse_fact(fact_dict)
                neutral_facts.append(neutral_fact)
                self.facts_processed += 1
            except Exception as e:
                self.errors.append({
                    'fact': fact_dict,
                    'error': str(e)
                })
        
        return neutral_facts
    
    def parse_fact(self, fact_dict: Dict[str, Any]) -> NeutralFact:
        """
        Parse a single Map Pro fact into neutral format.
        
        FIXED: Now uses taxonomy as primary source for period_type.
        """
        # Extract concept (Map Pro uses 'concept' field, not 'qname')
        raw_concept = fact_dict.get('concept')
        if not raw_concept:
            raw_concept = fact_dict.get('original_concept')
            if not raw_concept:
                raise ValueError("Missing both 'concept' and 'original_concept' fields")
        
        # Normalize concept ID (strip year suffix)
        concept_id = normalize_concept_id(raw_concept)
        concept_namespace = extract_namespace(concept_id)
        concept_local_name = extract_local_name(concept_id)
        
        # Extract label
        label = fact_dict.get('label', concept_local_name)
        
        # Extract value (preserve as string)
        value = str(fact_dict.get('value', ''))
        
        # Extract unit
        unit = fact_dict.get('unit')
        
        # Extract decimals
        decimals = fact_dict.get('decimals')
        
        # Extract context FIRST (needed for fallback inference)
        context_id = fact_dict.get('context', '')
        context_date = extract_date_from_context_id(context_id)
        
        # ========================================================================
        # CRITICAL FIX: Determine period_type using taxonomy as PRIMARY source
        # ========================================================================
        
        period_type = self._get_period_type(
            concept_id=concept_id,
            context_id=context_id,
            map_pro_metadata=fact_dict
        )
        
        # ========================================================================
        
        # Extract balance_type
        balance_type = fact_dict.get('balance_type')
        
        # Extract is_abstract
        is_abstract = fact_dict.get('is_abstract', False)
        
        # Determine if monetary
        is_monetary = self._is_monetary_fact(fact_dict)
        
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
            source_system='map_pro',
            original_format=fact_dict.copy(),
            adapter_version=self.adapter_version
        )
        
        # Validate
        is_valid, errors = validate_neutral_fact(neutral_fact)
        if not is_valid:
            raise ValueError(f"Invalid neutral fact: {errors}")
        
        return neutral_fact
    
    def _get_period_type(
        self,
        concept_id: str,
        context_id: str,
        map_pro_metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Determine period_type using hierarchical approach.
        
        Priority Order:
        1. Taxonomy lookup (MOST AUTHORITATIVE)
        2. Context pattern inference (FALLBACK)
        3. Map Pro metadata (LAST RESORT)
        
        Args:
            concept_id: Normalized concept ID (e.g., 'us-gaap:Assets')
            context_id: Context reference ID
            map_pro_metadata: Original Map Pro fact dictionary
            
        Returns:
            'instant', 'duration', or None
        """
        period_type = None
        
        # ========================================================================
        # PRIMARY: Lookup in taxonomy (MOST AUTHORITATIVE)
        # ========================================================================
        if self.taxonomy_loader and self.taxonomy_data:
            try:
                concept_info = self.taxonomy_loader.get_concept_info(
                    concept_id,
                    self.taxonomy_data
                )
                
                if concept_info and concept_info.get('exists'):
                    taxonomy_period_type = concept_info.get('period_type')
                    
                    if taxonomy_period_type:
                        period_type = taxonomy_period_type
                        self.period_type_sources['taxonomy'] += 1
                        return period_type
                        
            except Exception as e:
                # Log but don't fail - continue to fallback
                # In production, use proper logging
                pass
        
        # ========================================================================
        # SECONDARY: Infer from context pattern (FALLBACK)
        # ========================================================================
        if not period_type and context_id:
            if 'As_Of_' in context_id or 'as_of_' in context_id.lower():
                period_type = 'instant'
                self.period_type_sources['context_inference'] += 1
                return period_type
                
            elif 'Duration_' in context_id or 'duration_' in context_id.lower():
                period_type = 'duration'
                self.period_type_sources['context_inference'] += 1
                return period_type
                
            elif '_To_' in context_id or '_to_' in context_id.lower():
                # Duration contexts typically have "From...To..." pattern
                period_type = 'duration'
                self.period_type_sources['context_inference'] += 1
                return period_type
        
        # ========================================================================
        # TERTIARY: Use Map Pro's metadata (LAST RESORT)
        # ========================================================================
        if not period_type:
            period_type = map_pro_metadata.get('period_type')
            if period_type:
                self.period_type_sources['map_pro_metadata'] += 1
        
        return period_type
    
    def _is_monetary_fact(self, fact_dict: Dict[str, Any]) -> bool:
        """Determine if fact represents a monetary value."""
        unit = fact_dict.get('unit')
        if unit:
            unit_lower = unit.lower()
            if 'usd' in unit_lower or 'currency' in unit_lower:
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            'adapter': 'MapProAdapter',
            'version': self.adapter_version,
            'facts_processed': self.facts_processed,
            'errors_count': len(self.errors),
            'period_type_sources': self.period_type_sources,
            'errors': self.errors
        }


__all__ = ['MapProAdapter']


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

"""
# Old way (WITHOUT taxonomy):
adapter = MapProAdapter()
facts = adapter.parse_statement_file(Path('map_pro_balance_sheet.json'))

# New way (WITH taxonomy):
from ccq_mapper.loaders import TaxonomyLoader

# Load taxonomy once (reuse for all adapters)
taxonomy_loader = TaxonomyLoader()
taxonomy_data = taxonomy_loader.load_taxonomy(taxonomy_paths)

# Create adapter with taxonomy access
adapter = MapProAdapter(
    taxonomy_loader=taxonomy_loader,
    taxonomy_data=taxonomy_data
)

# Parse as usual
facts = adapter.parse_statement_file(Path('map_pro_balance_sheet.json'))

# Check how many period_types came from taxonomy vs inference
stats = adapter.get_statistics()
print(stats['period_type_sources'])
# Output: {'taxonomy': 850, 'context_inference': 100, 'map_pro_metadata': 50}
"""