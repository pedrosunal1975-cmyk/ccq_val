"""
Facts Validator for Fact Authority Engine.

Validates parsed_facts.json structure and content quality.
Provides detailed validation reporting for Map Pro data.
"""

from typing import Dict, List, Set
import logging


logger = logging.getLogger(__name__)


class FactsValidator:
    """
    Validate parsed facts structure and content.
    
    Provides detailed validation beyond basic structure checks,
    including fact completeness, consistency, and quality metrics.
    
    Key features:
    - Validates fact structure (required fields)
    - Checks for duplicate facts
    - Identifies incomplete facts
    - Validates company info
    - Provides validation statistics
    
    Usage:
        validator = FactsValidator()
        validation = validator.validate(facts_data)
        if validation['is_valid']:
            # Process facts
        else:
            # Handle errors: validation['errors']
    """
    
    # Required fields in each fact (with fallback support)
    # Support multiple naming conventions:
    # - concept_qname, qname, concept (for concept)
    # - fact_value, value (for value)
    # - context_ref, contextRef (for context)
    REQUIRED_FACT_FIELDS = {'concept_qname', 'fact_value', 'context_ref'}
    REQUIRED_FALLBACK = {
        'concept': ['concept_qname', 'qname', 'concept', 'concept_local_name'],
        'value': ['fact_value', 'value'],
        'context': ['context_ref', 'contextRef', 'context']
    }
    
    # Optional but commonly present fields (from filings_reader output)
    COMMON_FACT_FIELDS = {
        'unit', 'decimals', 'precision', 'label', 'id'
    }
    
    def __init__(self):
        """Initialize facts validator."""
        self.last_validation = None
    
    def validate(self, facts_data: Dict) -> Dict:
        """
        Validate parsed facts data.
        
        Args:
            facts_data: Parsed facts data from ParsedFactsLoader
            
        Returns:
            Dict with validation results:
            {
                'is_valid': bool,
                'errors': List[str],
                'warnings': List[str],
                'statistics': Dict,
                'completeness': Dict
            }
        """
        logger.debug("Validating parsed facts")
        
        errors = []
        warnings = []
        
        # Check top-level structure
        if 'facts' not in facts_data:
            errors.append("Missing 'facts' key in data")
            return {
                'is_valid': False,
                'errors': errors,
                'warnings': warnings,
                'statistics': {},
                'completeness': {}
            }
        
        facts = facts_data.get('facts', [])
        
        # Validate facts list
        if not isinstance(facts, list):
            errors.append(f"'facts' must be a list, got {type(facts)}")
        
        if not facts:
            warnings.append("Facts list is empty")
        
        # Validate company info / metadata
        metadata_errors = self._validate_company_info(facts_data.get('metadata', {}))
        errors.extend(metadata_errors)
        
        # Validate individual facts
        fact_errors, fact_warnings = self._validate_facts(facts)
        errors.extend(fact_errors)
        warnings.extend(fact_warnings)
        
        # Check for duplicates
        duplicate_warnings = self._check_duplicates(facts)
        warnings.extend(duplicate_warnings)
        
        # Generate statistics
        statistics = self._generate_statistics(facts)
        
        # Generate completeness report
        completeness = self._generate_completeness(facts)
        
        # Overall validation result
        is_valid = len(errors) == 0
        
        validation_result = {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'statistics': statistics,
            'completeness': completeness
        }
        
        self.last_validation = validation_result
        
        logger.info(
            f"Validation complete: {'PASS' if is_valid else 'FAIL'} "
            f"({len(errors)} errors, {len(warnings)} warnings)"
        )
        
        return validation_result
    
    def _validate_company_info(self, company_info: Dict) -> List[str]:
        """
        Validate company/metadata information.
        
        Args:
            company_info: Metadata dict
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Metadata is optional in some cases
        if not company_info:
            logger.debug("No metadata present (acceptable for some files)")
            return errors
        
        if not isinstance(company_info, dict):
            errors.append(f"metadata must be dict, got {type(company_info)}")
            return errors
        
        # Check for common fields (not strict requirements)
        expected_fields = {'company', 'cik', 'market'}
        missing_fields = expected_fields - set(company_info.keys())
        if missing_fields:
            logger.debug(f"metadata missing optional fields: {missing_fields}")
        
        return errors
    
    def _validate_facts(self, facts: List[Dict]) -> tuple[List[str], List[str]]:
        """
        Validate individual facts.
        
        Args:
            facts: List of fact dicts
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        for idx, fact in enumerate(facts):
            if not isinstance(fact, dict):
                errors.append(f"Fact {idx} is not a dict: {type(fact)}")
                continue
            
            # Check required fields using fallback pattern
            for field_type, field_names in self.REQUIRED_FALLBACK.items():
                has_field = any(fact.get(name) is not None for name in field_names)
                if not has_field:
                    errors.append(
                        f"Fact {idx} missing {field_type} "
                        f"(checked: {', '.join(field_names)})"
                    )
        
        return errors, warnings
    
    def _check_duplicates(self, facts: List[Dict]) -> List[str]:
        """
        Check for duplicate facts.
        
        Args:
            facts: List of fact dicts
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        seen = set()
        duplicates = []
        
        for fact in facts:
            # Create signature using fallback pattern
            concept = (
                fact.get('concept_qname') or
                fact.get('qname') or
                fact.get('concept')
            )
            context = (
                fact.get('context_ref') or
                fact.get('contextRef') or
                fact.get('context')
            )
            value = (
                fact.get('fact_value') or
                fact.get('value')
            )
            
            signature = (concept, context, str(value))
            
            if signature in seen:
                duplicates.append(signature)
            else:
                seen.add(signature)
        
        if duplicates:
            warnings.append(
                f"Found {len(duplicates)} duplicate facts "
                f"(same concept + context + value)"
            )
        
        return warnings
    
    def _generate_statistics(self, facts: List[Dict]) -> Dict:
        """
        Generate statistics about facts.
        
        Args:
            facts: List of fact dicts
            
        Returns:
            Dict with statistics
        """
        if not facts:
            return {
                'total_facts': 0,
                'unique_concepts': 0,
                'unique_contexts': 0,
                'facts_with_units': 0,
                'null_values': 0
            }
        
        concepts = set()
        contexts = set()
        with_units = 0
        null_values = 0
        
        for fact in facts:
            # Extract concept using fallback
            concept = (
                fact.get('concept_qname') or
                fact.get('qname') or
                fact.get('concept')
            )
            if concept:
                concepts.add(concept)
            
            # Extract context using fallback
            context = (
                fact.get('context_ref') or
                fact.get('contextRef') or
                fact.get('context')
            )
            if context:
                contexts.add(context)
            
            # Extract unit using fallback
            unit = fact.get('unit_ref') or fact.get('unit')
            if unit:
                with_units += 1
            
            # Extract value using fallback
            value = fact.get('fact_value') or fact.get('value')
            if value is None:
                null_values += 1
        
        return {
            'total_facts': len(facts),
            'unique_concepts': len(concepts),
            'unique_contexts': len(contexts),
            'facts_with_units': with_units,
            'null_values': null_values
        }
    
    def _generate_completeness(self, facts: List[Dict]) -> Dict:
        """
        Generate completeness report for facts.
        
        Args:
            facts: List of fact dicts
            
        Returns:
            Dict with completeness metrics
        """
        if not facts:
            return {
                'required_fields': 100.0,
                'common_fields': 0.0,
                'complete_facts': 0
            }
        
        total = len(facts)
        required_complete = 0
        common_complete = 0
        
        for fact in facts:
            fact_keys = set(fact.keys())
            
            # Check required fields
            if self.REQUIRED_FACT_FIELDS.issubset(fact_keys):
                required_complete += 1
            
            # Check common fields
            if self.COMMON_FACT_FIELDS.issubset(fact_keys):
                common_complete += 1
        
        return {
            'required_fields': (required_complete / total * 100),
            'common_fields': (common_complete / total * 100),
            'complete_facts': common_complete
        }
    
    def get_last_validation(self) -> Dict:
        """
        Get last validation result.
        
        Returns:
            Last validation dict, or empty dict if none
        """
        return self.last_validation or {}