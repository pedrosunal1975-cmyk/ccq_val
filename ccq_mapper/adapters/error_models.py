"""
Error Analysis Data Models
===========================

Location: ccq_val/engines/ccq_mapper/adapters/error_models.py

Defines data structures for error analysis.

Data Classes:
- ErrorDetail: Individual error information
- ErrorSummary: Aggregated error statistics for a statement
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class ErrorDetail:
    """Detailed information about a single parsing error."""
    
    error_type: str
    error_message: str
    concept: str
    namespace: str
    missing_fields: List[str]
    has_value: bool
    has_unit: bool
    has_context: bool
    full_fact: Dict
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'error_type': self.error_type,
            'error_message': self.error_message,
            'concept': self.concept,
            'namespace': self.namespace,
            'missing_fields': self.missing_fields,
            'has_value': self.has_value,
            'has_unit': self.has_unit,
            'has_context': self.has_context,
            'full_fact': self.full_fact
        }


@dataclass
class ErrorSummary:
    """Aggregated error statistics for a statement."""
    
    statement_type: str
    adapter_type: str
    total_facts: int
    successful_facts: int
    failed_facts: int
    error_rate: float
    error_categories: Dict[str, int] = field(default_factory=dict)
    missing_fields_freq: Dict[str, int] = field(default_factory=dict)
    problematic_namespaces: Dict[str, int] = field(default_factory=dict)
    sample_errors: List[ErrorDetail] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'statement_type': self.statement_type,
            'adapter_type': self.adapter_type,
            'total_facts': self.total_facts,
            'successful_facts': self.successful_facts,
            'failed_facts': self.failed_facts,
            'error_rate': self.error_rate,
            'error_categories': self.error_categories,
            'missing_fields_freq': self.missing_fields_freq,
            'problematic_namespaces': self.problematic_namespaces,
            'sample_errors': [e.to_dict() for e in self.sample_errors[:3]]
        }