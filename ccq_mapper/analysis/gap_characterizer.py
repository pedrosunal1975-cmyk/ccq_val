# File: engines/ccq_mapper/analysis/gap_characterizer.py

"""
CCQ Gap Characterizer
====================

Enriches classification gaps with comprehensive characterization.

Responsibilities:
- Analyze each gap fact for properties
- Determine what classifications are missing
- Assess financial significance
- Estimate best-guess statement placement
- Calculate priority level

Does NOT:
- Modify fact data
- Make classification decisions
- Access database
"""

from typing import Dict, Any, List
from core.system_logger import get_logger

logger = get_logger(__name__)


SIGNIFICANCE_CRITICAL = 'CRITICAL'
SIGNIFICANCE_HIGH = 'HIGH'
SIGNIFICANCE_MEDIUM = 'MEDIUM'
SIGNIFICANCE_LOW = 'LOW'

PRIORITY_P0 = 'P0'
PRIORITY_P1 = 'P1'
PRIORITY_P2 = 'P2'
PRIORITY_P3 = 'P3'


class GapCharacterizer:
    """
    Enriches gap facts with comprehensive characterization.
    
    Uses existing classifiers to understand what each gap represents
    and why classification failed.
    """
    
    def __init__(
        self,
        statement_classifier,
        monetary_classifier,
        temporal_classifier
    ):
        """
        Initialize gap characterizer.
        
        Args:
            statement_classifier: StatementClassifier instance (required)
            monetary_classifier: MonetaryClassifier instance (required)
            temporal_classifier: TemporalClassifier instance (required)
        """
        self.logger = logger
        
        if not statement_classifier or not monetary_classifier or not temporal_classifier:
            raise ValueError("All classifiers must be provided to GapCharacterizer")
        
        self.statement_classifier = statement_classifier
        self.monetary_classifier = monetary_classifier
        self.temporal_classifier = temporal_classifier
        
        self.logger.info("Gap characterizer initialized")
    
    def characterize_gaps(
        self,
        gap_facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich gap facts with comprehensive characterization.
        
        Args:
            gap_facts: List of facts with classification gaps
            
        Returns:
            List of enriched gap profiles
        """
        enriched_gaps = []
        
        for gap_fact in gap_facts:
            enriched = self._characterize_single_gap(gap_fact)
            enriched_gaps.append(enriched)
        
        return enriched_gaps
    
    def _characterize_single_gap(
        self,
        gap_fact: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Characterize a single gap fact.
        
        Args:
            gap_fact: Gap fact dictionary
            
        Returns:
            Enriched gap profile
        """
        fact = gap_fact.get('fact', {})
        gap_type = gap_fact.get('gap_type', 'unknown')
        reason = gap_fact.get('reason', '')
        
        # Extract basic info
        concept = self._extract_concept(fact)
        value = self._extract_value(fact)
        properties = fact.get('extracted_properties', {})
        classification = fact.get('classification', {})
        
        # Determine what we can infer from available properties
        available_properties = self._analyze_available_properties(properties)
        missing_classifications = self._identify_missing_classifications(
            classification
        )
        
        # Attempt best-guess classification
        best_guess = self._make_best_guess(properties, classification)
        
        # Assess significance
        significance = self._assess_significance(
            concept,
            properties,
            best_guess
        )
        
        # Calculate priority
        priority = self._calculate_priority(significance, gap_type)
        
        return {
            'concept': concept,
            'value': value,
            'gap_type': gap_type,
            'reason': reason,
            'available_properties': available_properties,
            'missing_classifications': missing_classifications,
            'best_guess_statement': best_guess.get('statement'),
            'best_guess_confidence': best_guess.get('confidence'),
            'significance': significance,
            'priority': priority,
            'impact_description': self._describe_impact(
                significance,
                gap_type,
                concept
            )
        }
    
    def _extract_concept(self, fact: Dict[str, Any]) -> str:
        """Extract concept from fact (handles nested structure)."""
        # Gap facts have structure: {'fact': {actual_data}, 'gap_type': '...'}
        # So we need to look in the nested 'fact' if it exists
        fact_data = fact if 'fact' not in fact else fact.get('fact', {})
        
        for field in ['concept_qname', 'concept', 'qname', 'name']:
            concept = fact_data.get(field)
            if concept:
                return str(concept)
        return 'unknown'
    
    def _extract_value(self, fact: Dict[str, Any]) -> Any:
        """Extract value from fact (handles nested structure)."""
        # Handle nested structure
        fact_data = fact if 'fact' not in fact else fact.get('fact', {})
        
        for field in ['fact_value', 'value', 'amount']:
            value = fact_data.get(field)
            if value is not None:
                return value
        return None
    
    def _analyze_available_properties(
        self,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze which properties are available.
        
        Args:
            properties: Extracted properties dictionary
            
        Returns:
            Summary of available properties
        """
        available = {}
        
        property_fields = [
            'period_type',
            'value_type',
            'unit',
            'balance',
            'decimals',
            'is_nil'
        ]
        
        for field in property_fields:
            value = properties.get(field)
            if value:
                available[field] = value
        
        return available
    
    def _identify_missing_classifications(
        self,
        classification: Dict[str, Any]
    ) -> List[str]:
        """
        Identify which classifications are missing or incomplete.
        
        Args:
            classification: Classification dictionary
            
        Returns:
            List of missing classification types
        """
        missing = []
        
        classification_fields = {
            'monetary_type': 'monetary classification',
            'temporal_type': 'temporal classification',
            'accounting_type': 'accounting classification',
            'predicted_statement': 'statement classification'
        }
        
        for field, description in classification_fields.items():
            value = classification.get(field)
            if not value or value in ['unknown', 'unclassified', 'other']:
                missing.append(description)
        
        return missing
    
    def _make_best_guess(
        self,
        properties: Dict[str, Any],
        existing_classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make best-guess statement classification based on available data.
        
        Args:
            properties: Extracted properties
            existing_classification: Partial classification
            
        Returns:
            Best guess with confidence score
        """
        # If statement already classified, use it
        existing_statement = existing_classification.get('predicted_statement')
        if existing_statement and existing_statement != 'unknown':
            return {
                'statement': existing_statement,
                'confidence': 0.8
            }
        
        # Try to classify based on properties
        if properties:
            try:
                statement = self.statement_classifier.classify(properties)
                if statement and statement != 'other':
                    return {
                        'statement': statement,
                        'confidence': 0.6
                    }
            except Exception:
                pass
        
        # Default to 'other'
        return {
            'statement': 'other',
            'confidence': 0.3
        }
    
    def _assess_significance(
        self,
        concept: str,
        properties: Dict[str, Any],
        best_guess: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess financial significance of the gap.
        
        Args:
            concept: Concept identifier
            properties: Extracted properties
            best_guess: Best guess classification
            
        Returns:
            Significance assessment
        """
        concept_lower = concept.lower()
        
        # Core financial statement concepts
        core_concepts = [
            'assets', 'liabilities', 'equity', 'stockholdersequity',
            'revenue', 'income', 'expense', 'netincome', 'grossprofit',
            'cash', 'earnings', 'ebitda'
        ]
        
        is_core = any(kw in concept_lower for kw in core_concepts)
        
        # Check if numeric/monetary
        value_type = properties.get('value_type', '')
        is_numeric = value_type == 'numeric'
        
        # Main statement vs other
        statement = best_guess.get('statement', 'other')
        is_main_statement = statement in [
            'balance_sheet',
            'income_statement',
            'cash_flow'
        ]
        
        # Determine significance level
        if is_core and is_numeric and is_main_statement:
            level = SIGNIFICANCE_CRITICAL
            reason = 'Core financial statement line item'
        elif is_numeric and is_main_statement:
            level = SIGNIFICANCE_HIGH
            reason = 'Financial statement numeric fact'
        elif is_numeric:
            level = SIGNIFICANCE_MEDIUM
            reason = 'Numeric financial data'
        else:
            level = SIGNIFICANCE_LOW
            reason = 'Non-numeric or supplementary data'
        
        return {
            'level': level,
            'reason': reason,
            'is_core_financial': is_core,
            'is_numeric': is_numeric,
            'is_main_statement': is_main_statement
        }
    
    def _calculate_priority(
        self,
        significance: Dict[str, Any],
        gap_type: str
    ) -> str:
        """
        Calculate priority level for gap resolution.
        
        Args:
            significance: Significance assessment
            gap_type: Type of gap
            
        Returns:
            Priority level (P0, P1, P2, P3)
        """
        sig_level = significance.get('level')
        
        if sig_level == SIGNIFICANCE_CRITICAL:
            return PRIORITY_P0
        elif sig_level == SIGNIFICANCE_HIGH:
            return PRIORITY_P1
        elif sig_level == SIGNIFICANCE_MEDIUM:
            return PRIORITY_P2
        else:
            return PRIORITY_P3
    
    def _describe_impact(
        self,
        significance: Dict[str, Any],
        gap_type: str,
        concept: str
    ) -> str:
        """
        Generate human-readable impact description.
        
        Args:
            significance: Significance assessment
            gap_type: Type of gap
            concept: Concept identifier
            
        Returns:
            Impact description string
        """
        sig_level = significance.get('level')
        is_core = significance.get('is_core_financial', False)
        
        if sig_level == SIGNIFICANCE_CRITICAL:
            return f"CRITICAL: Core financial concept unclassified - {concept}"
        elif sig_level == SIGNIFICANCE_HIGH:
            return f"HIGH: Financial statement fact unclassified - {concept}"
        elif sig_level == SIGNIFICANCE_MEDIUM:
            return f"MEDIUM: Numeric data unclassified - {concept}"
        else:
            return f"LOW: Supplementary data unclassified - {concept}"


__all__ = ['GapCharacterizer']