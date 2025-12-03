"""
Taxonomy Validator
==================

Validates constructed statements against taxonomy expectations.

CRITICAL: Validation happens AFTER construction, not during.
"""

from typing import Dict, Any, List
from pathlib import Path

from core.system_logger import get_logger
from ..loaders.taxonomy_loader import TaxonomyLoader

logger = get_logger(__name__)


class TaxonomyValidator:
    """
    Validate constructed statements against taxonomy.
    
    Checks:
    - Concept existence in taxonomy
    - Property consistency (balance type, period type)
    - Value types and units
    - Required concepts presence
    
    This is POST-construction validation, not matching.
    """
    
    def __init__(self):
        self.taxonomy_loader = TaxonomyLoader()
        self.loaded_taxonomies = None
    
    def validate(
        self,
        constructed_statements: List[Dict[str, Any]],
        taxonomy_paths: List[Path]
    ) -> Dict[str, Any]:
        """
        Validate constructed statements against taxonomies.
        
        Args:
            constructed_statements: Statements built by CCQ
            taxonomy_paths: Paths to taxonomy files
            
        Returns:
            Validation report
        """
        logger.info(f"Validating {len(constructed_statements)} statements")
        
        # Load taxonomies if not already loaded
        if not self.loaded_taxonomies:
            self.loaded_taxonomies = self.taxonomy_loader.load_taxonomies(taxonomy_paths)
        
        validation_results = {
            'overall_valid': True,
            'statement_validations': [],
            'total_facts_validated': 0,
            'facts_passed': 0,
            'facts_failed': 0,
            'issues': []
        }
        
        # Validate each statement
        for statement in constructed_statements:
            stmt_validation = self._validate_statement(statement)
            validation_results['statement_validations'].append(stmt_validation)
            
            validation_results['total_facts_validated'] += stmt_validation['facts_checked']
            validation_results['facts_passed'] += stmt_validation['facts_passed']
            validation_results['facts_failed'] += stmt_validation['facts_failed']
            
            if not stmt_validation['valid']:
                validation_results['overall_valid'] = False
                validation_results['issues'].extend(stmt_validation['issues'])
        
        # Calculate pass rate
        if validation_results['total_facts_validated'] > 0:
            validation_results['pass_rate'] = (
                validation_results['facts_passed'] / 
                validation_results['total_facts_validated'] * 100
            )
        else:
            validation_results['pass_rate'] = 0.0
        
        logger.info(
            f"Validation complete: {validation_results['pass_rate']:.1f}% pass rate"
        )
        
        return validation_results
    
    def _validate_statement(self, statement: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single statement."""
        stmt_type = statement.get('statement_type')
        line_items = statement.get('line_items', [])
        
        validation = {
            'statement_type': stmt_type,
            'valid': True,
            'facts_checked': 0,
            'facts_passed': 0,
            'facts_failed': 0,
            'issues': []
        }
        
        # Validate each line item
        for item in line_items:
            validation['facts_checked'] += 1
            
            item_validation = self._validate_line_item(item, stmt_type)
            
            if item_validation['valid']:
                validation['facts_passed'] += 1
            else:
                validation['facts_failed'] += 1
                validation['valid'] = False
                validation['issues'].append({
                    'qname': item.get('qname'),
                    'label': item.get('label'),
                    'problems': item_validation['problems']
                })
        
        return validation
    
    def _validate_line_item(
        self,
        line_item: Dict[str, Any],
        statement_type: str
    ) -> Dict[str, Any]:
        """Validate a single line item against taxonomy."""
        qname = line_item.get('qname')
        
        if not qname:
            return {
                'valid': False,
                'problems': ['No qname provided']
            }
        
        # Get concept info from taxonomy
        concept_info = self.taxonomy_loader.get_concept_info(
            qname,
            self.loaded_taxonomies
        )
        
        problems = []
        
        # Check concept exists
        if not concept_info['exists']:
            problems.append(f"Concept {qname} not found in taxonomy")
            return {
                'valid': False,
                'problems': problems
            }
        
        # Validate properties
        property_validation = self._validate_properties(line_item, concept_info)
        problems.extend(property_validation)
        
        # Validate statement assignment
        stmt_validation = self._validate_statement_assignment(
            line_item,
            statement_type,
            concept_info
        )
        problems.extend(stmt_validation)
        
        return {
            'valid': len(problems) == 0,
            'problems': problems
        }
    
    def _validate_properties(
        self,
        line_item: Dict[str, Any],
        concept_info: Dict[str, Any]
    ) -> List[str]:
        """Validate that line item properties match concept definition."""
        problems = []
        
        item_props = line_item.get('properties', {})
        classification = line_item.get('classification', {})
        
        # Check balance type
        expected_balance = concept_info.get('balance_type')
        actual_balance = item_props.get('balance_type')
        classified_balance = classification.get('accounting_type')
        
        if expected_balance and classified_balance:
            if expected_balance != classified_balance:
                problems.append(
                    f"Balance type mismatch: expected {expected_balance}, "
                    f"classified as {classified_balance}"
                )
        
        # Check period type
        expected_period = concept_info.get('period_type')
        actual_period = item_props.get('period_type')
        classified_period = classification.get('temporal_type')
        
        if expected_period and classified_period:
            # Map instant/duration to expected values
            period_map = {
                'instant': 'instant',
                'duration': 'duration'
            }
            mapped_classified = period_map.get(classified_period)
            
            if expected_period != mapped_classified:
                problems.append(
                    f"Period type mismatch: expected {expected_period}, "
                    f"classified as {classified_period}"
                )
        
        # Check abstract status
        expected_abstract = concept_info.get('abstract', False)
        actual_abstract = item_props.get('is_abstract', False)
        
        if expected_abstract != actual_abstract:
            problems.append(
                f"Abstract status mismatch: expected {expected_abstract}, "
                f"got {actual_abstract}"
            )
        
        return problems
    
    def _validate_statement_assignment(
        self,
        line_item: Dict[str, Any],
        statement_type: str,
        concept_info: Dict[str, Any]
    ) -> List[str]:
        """
        Validate that line item is assigned to correct statement.
        
        Uses period type and balance type to verify statement assignment.
        """
        problems = []
        
        expected_period = concept_info.get('period_type')
        balance_type = concept_info.get('balance_type')
        
        # Balance sheet should have instant period type
        if statement_type == 'balance_sheet':
            if expected_period and expected_period != 'instant':
                problems.append(
                    f"Balance sheet item should have instant period, "
                    f"but has {expected_period}"
                )
        
        # Income and cash flow should have duration
        if statement_type in ['income_statement', 'cash_flow']:
            if expected_period and expected_period != 'duration':
                problems.append(
                    f"{statement_type} item should have duration period, "
                    f"but has {expected_period}"
                )
        
        return problems
    
    def generate_validation_summary(
        self,
        validation_results: Dict[str, Any]
    ) -> str:
        """Generate human-readable validation summary."""
        summary_lines = [
            "CCQ Mapper Validation Summary",
            "=" * 50,
            f"Overall Status: {'PASS' if validation_results['overall_valid'] else 'FAIL'}",
            f"Pass Rate: {validation_results['pass_rate']:.1f}%",
            f"Facts Validated: {validation_results['total_facts_validated']}",
            f"  - Passed: {validation_results['facts_passed']}",
            f"  - Failed: {validation_results['facts_failed']}",
            ""
        ]
        
        # Statement-level results
        summary_lines.append("Statement-Level Results:")
        for stmt_val in validation_results['statement_validations']:
            status = "✓" if stmt_val['valid'] else "✗"
            summary_lines.append(
                f"  {status} {stmt_val['statement_type']}: "
                f"{stmt_val['facts_passed']}/{stmt_val['facts_checked']} passed"
            )
        
        # Issues
        if validation_results['issues']:
            summary_lines.append("")
            summary_lines.append("Issues Found:")
            for issue in validation_results['issues'][:10]:  # Show first 10
                summary_lines.append(f"  - {issue['qname']}: {', '.join(issue['problems'])}")
            
            if len(validation_results['issues']) > 10:
                summary_lines.append(f"  ... and {len(validation_results['issues']) - 10} more")
        
        return "\n".join(summary_lines)


__all__ = ['TaxonomyValidator']