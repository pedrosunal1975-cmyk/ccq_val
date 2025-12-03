"""
Taxonomy Validator
==================

Validates taxonomy consistency and integrity.

Performs comprehensive checks on taxonomy structures including:
- Reference integrity (all referenced concepts exist)
- Calculation consistency (children exist for parents)
- Dimensional integrity (axes, domains, members are valid)
- Label coverage (concepts have labels)
- Type consistency (types are properly defined)

This enables quality assurance for custom taxonomies and debugging.

Classes:
    TaxonomyValidator: Validates taxonomy structures
"""

from pathlib import Path
from typing import Dict, List, Tuple, Set, Any
import logging


logger = logging.getLogger(__name__)


class TaxonomyValidator:
    """
    Validates taxonomy structures for consistency and integrity.
    
    Performs various validation checks to ensure the taxonomy is
    well-formed and complete. Useful for custom taxonomies and debugging.
    """
    
    def __init__(self):
        """Initialize taxonomy validator."""
        pass
    
    def validate_taxonomy(
        self,
        profile: 'TaxonomyProfile'
    ) -> Dict[str, List[str]]:
        """
        Perform comprehensive taxonomy validation.
        
        Args:
            profile: TaxonomyProfile to validate
            
        Returns:
            Dictionary of validation results:
            {
                'errors': ['Critical error 1', 'Critical error 2', ...],
                'warnings': ['Warning 1', 'Warning 2', ...],
                'info': ['Info message 1', 'Info message 2', ...],
                'summary': {
                    'total_checks': 10,
                    'passed': 8,
                    'warnings': 2,
                    'errors': 0
                }
            }
        """
        errors = []
        warnings = []
        info = []
        total_checks = 0
        
        # Check 1: Element reference integrity
        total_checks += 1
        ref_errors = self._check_element_references(profile)
        if ref_errors:
            errors.extend(ref_errors)
        
        # Check 2: Calculation integrity
        total_checks += 1
        calc_issues = self._check_calculation_integrity(profile)
        warnings.extend(calc_issues)
        
        # Check 3: Dimensional integrity
        total_checks += 1
        dim_issues = self._check_dimensional_integrity(profile)
        warnings.extend(dim_issues)
        
        # Check 4: Label coverage
        total_checks += 1
        label_info = self._check_label_coverage(profile)
        info.extend(label_info)
        
        # Check 5: Role definitions
        total_checks += 1
        role_issues = self._check_role_definitions(profile)
        if role_issues:
            warnings.extend(role_issues)
        
        # Calculate summary
        passed = total_checks - len(errors) - (1 if warnings else 0)
        
        return {
            'errors': errors,
            'warnings': warnings,
            'info': info,
            'summary': {
                'total_checks': total_checks,
                'passed': passed,
                'warnings': len(warnings),
                'errors': len(errors)
            }
        }
    
    def _check_element_references(
        self,
        profile: 'TaxonomyProfile'
    ) -> List[str]:
        """
        Check that all referenced elements exist.
        
        Args:
            profile: TaxonomyProfile to check
            
        Returns:
            List of error messages
        """
        errors = []
        elements = profile.elements
        element_set = set(elements.keys())
        
        # Check calculations reference valid elements
        for role, role_calcs in profile.calculations.items():
            for parent, parent_data in role_calcs.items():
                if parent not in element_set:
                    errors.append(
                        f"Calculation references undefined parent: {parent}"
                    )
                
                for child_data in parent_data.get('children', []):
                    child = child_data.get('concept')
                    if child and child not in element_set:
                        errors.append(
                            f"Calculation references undefined child: {child}"
                        )
        
        # Check dimensions reference valid elements
        dimensions = profile.dimensions
        
        for axis, axis_data in dimensions.get('axes', {}).items():
            if axis not in element_set:
                errors.append(
                    f"Axis not defined in elements: {axis}"
                )
            
            domain = axis_data.get('domain')
            if domain and domain not in element_set:
                errors.append(
                    f"Domain not defined in elements: {domain}"
                )
            
            for member in axis_data.get('members', []):
                if member not in element_set:
                    errors.append(
                        f"Member not defined in elements: {member}"
                    )
        
        return errors
    
    def _check_calculation_integrity(
        self,
        profile: 'TaxonomyProfile'
    ) -> List[str]:
        """
        Check calculation relationships for consistency.
        
        Args:
            profile: TaxonomyProfile to check
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        for role, role_calcs in profile.calculations.items():
            for parent, parent_data in role_calcs.items():
                children = parent_data.get('children', [])
                
                # Warn if no children
                if not children:
                    warnings.append(
                        f"Calculation parent has no children: {parent} in {role}"
                    )
                
                # Warn if only one child
                if len(children) == 1:
                    warnings.append(
                        f"Calculation parent has only one child: {parent} in {role}"
                    )
                
                # Check weight consistency
                weights = [c.get('weight', 1.0) for c in children]
                if all(w > 0 for w in weights):
                    pass  # All additions - normal
                elif all(w < 0 for w in weights):
                    warnings.append(
                        f"Calculation has all negative weights: {parent} in {role}"
                    )
        
        return warnings
    
    def _check_dimensional_integrity(
        self,
        profile: 'TaxonomyProfile'
    ) -> List[str]:
        """
        Check dimensional relationships for consistency.
        
        Args:
            profile: TaxonomyProfile to check
            
        Returns:
            List of warning messages
        """
        warnings = []
        dimensions = profile.dimensions
        
        # Check axes have domains
        for axis, axis_data in dimensions.get('axes', {}).items():
            if not axis_data.get('domain'):
                warnings.append(
                    f"Axis has no domain defined: {axis}"
                )
            
            # Warn if axis has no members
            if not axis_data.get('members'):
                warnings.append(
                    f"Axis has no members defined: {axis}"
                )
        
        # Check hypercubes reference valid axes
        axes_set = set(dimensions.get('axes', {}).keys())
        
        for hypercube, hypercube_data in dimensions.get('hypercubes', {}).items():
            for dimension in hypercube_data.get('dimensions', []):
                if dimension not in axes_set:
                    warnings.append(
                        f"Hypercube references undefined axis: {dimension} in {hypercube}"
                    )
            
            # Warn if hypercube has no dimensions
            if not hypercube_data.get('dimensions'):
                warnings.append(
                    f"Hypercube has no dimensions: {hypercube}"
                )
        
        return warnings
    
    def _check_label_coverage(
        self,
        profile: 'TaxonomyProfile'
    ) -> List[str]:
        """
        Check label coverage for elements.
        
        Args:
            profile: TaxonomyProfile to check
            
        Returns:
            List of info messages
        """
        info = []
        elements = profile.elements
        labels = profile.labels
        
        if not labels:
            info.append("No labels found in taxonomy")
            return info
        
        # Calculate coverage
        total_elements = len(elements)
        labeled_elements = len(labels)
        coverage = (labeled_elements / total_elements * 100) if total_elements > 0 else 0
        
        info.append(f"Label coverage: {coverage:.1f}% ({labeled_elements}/{total_elements})")
        
        # Check for standard label coverage
        with_standard = sum(
            1 for concept_labels in labels.values()
            if 'standard' in concept_labels
        )
        
        standard_coverage = (with_standard / total_elements * 100) if total_elements > 0 else 0
        info.append(
            f"Standard label coverage: {standard_coverage:.1f}% ({with_standard}/{total_elements})"
        )
        
        return info
    
    def _check_role_definitions(
        self,
        profile: 'TaxonomyProfile'
    ) -> List[str]:
        """
        Check role definitions for consistency.
        
        Args:
            profile: TaxonomyProfile to check
            
        Returns:
            List of warning messages
        """
        warnings = []
        roles = profile.roles
        
        # Check roles have required properties
        for role_uri, role_data in roles.items():
            if not role_data.get('definition'):
                warnings.append(
                    f"Role has no definition: {role_uri}"
                )
            
            if not role_data.get('type'):
                warnings.append(
                    f"Role has no type: {role_uri}"
                )
        
        return warnings
    
    def validate_element(
        self,
        profile: 'TaxonomyProfile',
        concept: str
    ) -> Dict[str, Any]:
        """
        Validate a specific element.
        
        Args:
            profile: TaxonomyProfile to check
            concept: Concept QName to validate
            
        Returns:
            Dictionary with validation results
        """
        issues = []
        
        # Check element exists
        if concept not in profile.elements:
            return {
                'exists': False,
                'issues': [f"Concept not found: {concept}"]
            }
        
        element = profile.elements[concept]
        
        # Check required properties
        if not element.get('type'):
            issues.append("Missing type")
        
        if element.get('abstract') == False:
            # Concrete element - should have period type
            if not element.get('period_type'):
                issues.append("Concrete element missing period_type")
            
            # Monetary elements should have balance
            if element.get('base_type') == 'monetary' and not element.get('balance'):
                issues.append("Monetary element missing balance")
        
        # Check labels
        has_label = concept in profile.labels
        if not has_label:
            issues.append("No label defined")
        
        return {
            'exists': True,
            'properties': element,
            'has_label': has_label,
            'issues': issues
        }
    
    def get_validation_summary(
        self,
        validation_results: Dict[str, List[str]]
    ) -> str:
        """
        Get human-readable validation summary.
        
        Args:
            validation_results: Results from validate_taxonomy()
            
        Returns:
            Formatted summary string
        """
        summary = validation_results['summary']
        errors = validation_results['errors']
        warnings = validation_results['warnings']
        
        lines = []
        lines.append("="*70)
        lines.append("TAXONOMY VALIDATION SUMMARY")
        lines.append("="*70)
        lines.append("")
        
        lines.append(f"Total checks:    {summary['total_checks']}")
        lines.append(f"Passed:          {summary['passed']}")
        lines.append(f"Warnings:        {summary['warnings']}")
        lines.append(f"Errors:          {summary['errors']}")
        lines.append("")
        
        if errors:
            lines.append("ERRORS:")
            for error in errors[:10]:  # Show first 10
                lines.append(f"  ❌ {error}")
            if len(errors) > 10:
                lines.append(f"  ... and {len(errors) - 10} more errors")
            lines.append("")
        
        if warnings:
            lines.append("WARNINGS:")
            for warning in warnings[:10]:  # Show first 10
                lines.append(f"  ⚠️  {warning}")
            if len(warnings) > 10:
                lines.append(f"  ... and {len(warnings) - 10} more warnings")
            lines.append("")
        
        if not errors and not warnings:
            lines.append("✅ No issues found - taxonomy is valid!")
            lines.append("")
        
        return "\n".join(lines)