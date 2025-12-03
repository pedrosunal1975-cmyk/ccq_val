"""
Neutral Format Specification
=============================

Common data structure for representing financial statement facts.
Both Map Pro and CCQ adapters translate to this neutral format before comparison.

Location: engines/ccq_mapper/adapters/neutral_format.py
"""

import re
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class NeutralFact:
    """
    Neutral representation of a financial statement fact.
    
    This format is independent of either Map Pro or CCQ's native structure.
    It serves as the common language for comparison.
    
    All adapters must translate their native format into this structure.
    """
    
    # ========================================================================
    # CONCEPT IDENTITY
    # ========================================================================
    
    concept_id: str
    """Normalized concept identifier (e.g., 'us-gaap:Assets')."""
    
    concept_namespace: str
    """Namespace prefix (e.g., 'us-gaap', 'plug', 'ifrs')."""
    
    concept_local_name: str
    """Local concept name without namespace (e.g., 'Assets')."""
    
    # ========================================================================
    # DISPLAY
    # ========================================================================
    
    label: str
    """Human-readable label for the concept."""
    
    # ========================================================================
    # VALUE
    # ========================================================================
    
    value: str
    """Fact value as string (preserves original precision)."""
    
    unit: Optional[str] = None
    """Unit of measurement (e.g., 'USD', 'shares', 'pure')."""
    
    decimals: Optional[str] = None
    """Decimal precision indicator."""
    
    # ========================================================================
    # CLASSIFICATION
    # ========================================================================
    
    period_type: Optional[str] = None
    """Period type: 'instant' or 'duration'."""
    
    balance_type: Optional[str] = None
    """Balance type: 'debit', 'credit', or None."""
    
    is_abstract: bool = False
    """Whether concept is abstract (no value, structural only)."""
    
    is_monetary: bool = False
    """Whether value represents monetary amount."""
    
    # ========================================================================
    # CONTEXT
    # ========================================================================
    
    context_id: str = ""
    """Context reference ID."""
    
    context_date: Optional[str] = None
    """Extracted date from context (YYYY-MM-DD format)."""
    
    context_period_start: Optional[str] = None
    """Period start date for duration facts (YYYY-MM-DD format)."""
    
    context_period_end: Optional[str] = None
    """Period end date (YYYY-MM-DD format)."""
    
    # ========================================================================
    # PROVENANCE (CRITICAL FOR DEBUGGING)
    # ========================================================================
    
    source_system: str = ""
    """Source system: 'map_pro' or 'ccq'."""
    
    original_format: Dict[str, Any] = field(default_factory=dict)
    """Complete original item as-is from source system."""
    
    adapter_version: str = "1.0.0"
    """Version of adapter that created this neutral fact."""
    
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    """Timestamp when neutral fact was created."""
    
    # ========================================================================
    # METADATA
    # ========================================================================
    
    statement_type: Optional[str] = None
    """Statement type: 'balance_sheet', 'income_statement', 'cash_flow', 'other'."""
    
    notes: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata or notes from adapter."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NeutralFact':
        """Create from dictionary."""
        return cls(**data)


# ============================================================================
# NORMALIZATION FUNCTIONS
# ============================================================================

def normalize_concept_id(concept: str) -> str:
    """
    Normalize concept ID by removing year suffix.
    
    Examples:
        us-gaap-2024:Assets -> us-gaap:Assets
        dei-2023:EntityName -> dei:EntityName
        plug:CustomConcept -> plug:CustomConcept (unchanged)
    
    Args:
        concept: Concept identifier with potential year suffix
        
    Returns:
        Normalized concept identifier without year suffix
    """
    if not concept or ':' not in concept:
        return concept
    
    # Pattern: namespace-YYYY:concept -> namespace:concept
    return re.sub(r'-\d{4}:', ':', concept)


def extract_namespace(concept_id: str) -> str:
    """
    Extract namespace from concept ID.
    
    Examples:
        us-gaap:Assets -> us-gaap
        plug:CustomConcept -> plug
        
    Args:
        concept_id: Concept identifier
        
    Returns:
        Namespace prefix
    """
    if ':' in concept_id:
        return concept_id.split(':', 1)[0]
    return ''


def extract_local_name(concept_id: str) -> str:
    """
    Extract local name from concept ID.
    
    Examples:
        us-gaap:Assets -> Assets
        plug:CustomConcept -> CustomConcept
        
    Args:
        concept_id: Concept identifier
        
    Returns:
        Local concept name
    """
    if ':' in concept_id:
        return concept_id.split(':', 1)[1]
    return concept_id


def extract_date_from_context_id(context_id: str) -> Optional[str]:
    """
    Extract date from context ID string.
    
    Handles formats like:
        As_Of_12_31_2024_...
        Duration_1_1_2024_To_12_31_2024_...
        
    Args:
        context_id: Context ID string
        
    Returns:
        Date in YYYY-MM-DD format or None
    """
    if not context_id:
        return None
    
    # Try instant context: As_Of_MM_DD_YYYY_...
    if 'As_Of_' in context_id:
        parts = context_id.split('As_Of_')[1].split('_')
        if len(parts) >= 3:
            try:
                month, day, year = parts[0], parts[1], parts[2]
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except (ValueError, IndexError):
                pass
    
    # Try duration context: Duration_M_D_YYYY_To_M_D_YYYY_...
    if 'Duration_' in context_id and '_To_' in context_id:
        try:
            # Extract the end date (second date)
            parts = context_id.split('_To_')[1].split('_')
            if len(parts) >= 3:
                month, day, year = parts[0], parts[1], parts[2]
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except (ValueError, IndexError):
            pass
    
    return None


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_neutral_fact(fact: NeutralFact) -> tuple[bool, list[str]]:
    """
    Validate that a neutral fact has all required fields.
    
    Args:
        fact: NeutralFact to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    if not fact.concept_id:
        errors.append("Missing concept_id")
    if not fact.concept_namespace:
        errors.append("Missing concept_namespace")
    if not fact.concept_local_name:
        errors.append("Missing concept_local_name")
    if not fact.label:
        errors.append("Missing label")
    if not fact.source_system:
        errors.append("Missing source_system")
    if not fact.original_format:
        errors.append("Missing original_format (must preserve source data)")
    
    # Validate source_system
    if fact.source_system not in ['map_pro', 'ccq']:
        errors.append(f"Invalid source_system: {fact.source_system}")
    
    # Validate period_type
    if fact.period_type and fact.period_type not in ['instant', 'duration']:
        errors.append(f"Invalid period_type: {fact.period_type}")
    
    # Validate balance_type
    if fact.balance_type and fact.balance_type not in ['debit', 'credit']:
        errors.append(f"Invalid balance_type: {fact.balance_type}")
    
    return (len(errors) == 0, errors)


__all__ = [
    'NeutralFact',
    'normalize_concept_id',
    'extract_namespace',
    'extract_local_name',
    'extract_date_from_context_id',
    'validate_neutral_fact',
]