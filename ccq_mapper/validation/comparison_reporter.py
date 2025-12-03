"""
Comparison Reporter
===================

Compares CCQ output with Map Pro output for validation.

CRITICAL: This is where we verify independent agreement.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal

from core.system_logger import get_logger

logger = get_logger(__name__)


class ComparisonReporter:
    """
    Compare CCQ constructed statements with Map Pro mapped statements.
    
    Compares:
    - Concept assignments
    - Values
    - Statement classifications
    - Structure
    
    Agreement = validation success
    Disagreement = investigation needed
    """
    
    TOLERANCE = Decimal('0.01')  # 1 cent tolerance for value comparison
    
    def generate_report(
        self,
        ccq_statements: List[Dict[str, Any]],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comparison report.
        
        Args:
            ccq_statements: Statements constructed by CCQ
            validation_results: Taxonomy validation results
            
        Returns:
            Comparison report dictionary
        """
        logger.info("Generating comparison report")
        
        report = {
            'ccq_method': 'property_based_classification',
            'timestamp': validation_results.get('timestamp'),
            'statements': self._summarize_statements(ccq_statements),
            'validation': {
                'pass_rate': validation_results.get('pass_rate', 0),
                'facts_validated': validation_results.get('total_facts_validated', 0),
                'facts_passed': validation_results.get('facts_passed', 0),
                'facts_failed': validation_results.get('facts_failed', 0)
            },
            'quality_metrics': self._calculate_quality_metrics(
                ccq_statements,
                validation_results
            )
        }
        
        return report
    
    def compare_with_map_pro(
        self,
        ccq_statements: List[Dict[str, Any]],
        map_pro_statements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare CCQ output with Map Pro output.
        
        Args:
            ccq_statements: CCQ constructed statements
            map_pro_statements: Map Pro mapped statements
            
        Returns:
            Detailed comparison report
        """
        logger.info("Comparing CCQ output with Map Pro output")
        
        comparison = {
            'overall_agreement': None,
            'statement_comparisons': [],
            'concept_agreements': [],
            'concept_disagreements': [],
            'value_differences': [],
            'agreement_rate': 0.0
        }
        
        # Match statements by type
        matched_statements = self._match_statements(ccq_statements, map_pro_statements)
        
        total_concepts = 0
        agreed_concepts = 0
        
        # Compare each matched statement
        for ccq_stmt, map_pro_stmt in matched_statements:
            stmt_comparison = self._compare_statements(ccq_stmt, map_pro_stmt)
            comparison['statement_comparisons'].append(stmt_comparison)
            
            total_concepts += stmt_comparison['total_concepts']
            agreed_concepts += stmt_comparison['agreed_concepts']
            
            comparison['concept_agreements'].extend(stmt_comparison['agreements'])
            comparison['concept_disagreements'].extend(stmt_comparison['disagreements'])
            comparison['value_differences'].extend(stmt_comparison['value_differences'])
        
        # Calculate agreement rate
        if total_concepts > 0:
            comparison['agreement_rate'] = (agreed_concepts / total_concepts) * 100
        
        comparison['overall_agreement'] = comparison['agreement_rate'] >= 90.0
        
        logger.info(f"Agreement rate: {comparison['agreement_rate']:.1f}%")
        
        return comparison
    
    def _summarize_statements(
        self,
        statements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Summarize constructed statements."""
        summaries = []
        
        for stmt in statements:
            summaries.append({
                'type': stmt.get('statement_type'),
                'name': stmt.get('statement_name'),
                'line_item_count': len(stmt.get('line_items', [])),
                'period': stmt.get('period'),
                'construction_method': stmt.get('construction_method')
            })
        
        return summaries
    
    def _calculate_quality_metrics(
        self,
        statements: List[Dict[str, Any]],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate quality metrics for CCQ output."""
        total_line_items = sum(
            len(stmt.get('line_items', []))
            for stmt in statements
        )
        
        return {
            'total_statements': len(statements),
            'total_line_items': total_line_items,
            'validation_pass_rate': validation_results.get('pass_rate', 0),
            'avg_items_per_statement': (
                total_line_items / len(statements) if statements else 0
            ),
            'completeness_score': self._calculate_completeness(statements)
        }
    
    def _calculate_completeness(self, statements: List[Dict[str, Any]]) -> float:
        """
        Calculate completeness score.
        
        Checks for presence of expected key statements.
        """
        expected_statements = {'balance_sheet', 'income_statement', 'cash_flow'}
        found_statements = {stmt.get('statement_type') for stmt in statements}
        
        overlap = expected_statements & found_statements
        
        return (len(overlap) / len(expected_statements)) * 100
    
    def _match_statements(
        self,
        ccq_statements: List[Dict[str, Any]],
        map_pro_statements: List[Dict[str, Any]]
    ) -> List[tuple]:
        """Match CCQ statements with Map Pro statements by type."""
        matches = []
        
        # Create lookup by statement type
        map_pro_by_type = {
            stmt.get('statement_type'): stmt
            for stmt in map_pro_statements
        }
        
        # Match CCQ statements
        for ccq_stmt in ccq_statements:
            stmt_type = ccq_stmt.get('statement_type')
            map_pro_stmt = map_pro_by_type.get(stmt_type)
            
            if map_pro_stmt:
                matches.append((ccq_stmt, map_pro_stmt))
        
        return matches
    
    def _compare_statements(
        self,
        ccq_stmt: Dict[str, Any],
        map_pro_stmt: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare two statements (CCQ vs Map Pro)."""
        comparison = {
            'statement_type': ccq_stmt.get('statement_type'),
            'total_concepts': 0,
            'agreed_concepts': 0,
            'agreements': [],
            'disagreements': [],
            'value_differences': []
        }
        
        # Build concept lookups
        ccq_concepts = self._build_concept_lookup(ccq_stmt)
        map_pro_concepts = self._build_concept_lookup(map_pro_stmt)
        
        # Compare common concepts
        common_qnames = set(ccq_concepts.keys()) & set(map_pro_concepts.keys())
        comparison['total_concepts'] = len(common_qnames)
        
        for qname in common_qnames:
            ccq_item = ccq_concepts[qname]
            map_pro_item = map_pro_concepts[qname]
            
            concept_comparison = self._compare_line_items(ccq_item, map_pro_item)
            
            if concept_comparison['agreed']:
                comparison['agreed_concepts'] += 1
                comparison['agreements'].append(concept_comparison)
            else:
                comparison['disagreements'].append(concept_comparison)
            
            if concept_comparison['value_difference']:
                comparison['value_differences'].append(concept_comparison)
        
        return comparison
    
    def _build_concept_lookup(self, statement: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Build qname -> line_item lookup."""
        lookup = {}
        
        for item in statement.get('line_items', []):
            qname = item.get('qname')
            if qname:
                lookup[qname] = item
        
        return lookup
    
    def _compare_line_items(
        self,
        ccq_item: Dict[str, Any],
        map_pro_item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare two line items."""
        qname = ccq_item.get('qname')
        
        # Compare values
        ccq_value = self._parse_value(ccq_item.get('value'))
        map_pro_value = self._parse_value(map_pro_item.get('value'))
        
        value_match = False
        value_diff = None
        
        if ccq_value is not None and map_pro_value is not None:
            value_diff = abs(ccq_value - map_pro_value)
            value_match = value_diff <= self.TOLERANCE
        elif ccq_value is None and map_pro_value is None:
            value_match = True
        
        # Compare classifications
        ccq_class = ccq_item.get('classification', {})
        map_pro_class = map_pro_item.get('classification', {})
        
        classification_match = (
            ccq_class.get('statement') == map_pro_class.get('statement') and
            ccq_class.get('accounting_type') == map_pro_class.get('accounting_type')
        )
        
        agreed = value_match and classification_match
        
        return {
            'qname': qname,
            'label': ccq_item.get('label'),
            'agreed': agreed,
            'value_match': value_match,
            'classification_match': classification_match,
            'ccq_value': float(ccq_value) if ccq_value is not None else None,
            'map_pro_value': float(map_pro_value) if map_pro_value is not None else None,
            'value_difference': float(value_diff) if value_diff else None
        }
    
    def _parse_value(self, value: Any) -> Optional[Decimal]:
        """Parse value to Decimal for comparison."""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            elif isinstance(value, str):
                # Remove commas and parse
                cleaned = value.replace(',', '')
                return Decimal(cleaned)
            elif isinstance(value, Decimal):
                return value
        except (ValueError, TypeError):
            return None
        
        return None
    
    def generate_comparison_summary(self, comparison: Dict[str, Any]) -> str:
        """Generate human-readable comparison summary."""
        lines = [
            "CCQ vs Map Pro Comparison Summary",
            "=" * 60,
            f"Overall Agreement: {'YES' if comparison['overall_agreement'] else 'NO'}",
            f"Agreement Rate: {comparison['agreement_rate']:.1f}%",
            f"Concepts Compared: {len(comparison['concept_agreements']) + len(comparison['concept_disagreements'])}",
            f"  - Agreements: {len(comparison['concept_agreements'])}",
            f"  - Disagreements: {len(comparison['concept_disagreements'])}",
            ""
        ]
        
        # Statement-level results
        lines.append("Statement-Level Comparison:")
        for stmt_comp in comparison['statement_comparisons']:
            rate = (stmt_comp['agreed_concepts'] / stmt_comp['total_concepts'] * 100
                   if stmt_comp['total_concepts'] > 0 else 0)
            lines.append(
                f"  {stmt_comp['statement_type']}: "
                f"{stmt_comp['agreed_concepts']}/{stmt_comp['total_concepts']} "
                f"({rate:.1f}%)"
            )
        
        # Value differences
        if comparison['value_differences']:
            lines.append("")
            lines.append("Significant Value Differences:")
            for diff in comparison['value_differences'][:5]:
                lines.append(
                    f"  {diff['qname']}: "
                    f"CCQ={diff['ccq_value']}, "
                    f"Map Pro={diff['map_pro_value']}, "
                    f"Diff={diff['value_difference']}"
                )
        
        # Disagreements
        if comparison['concept_disagreements']:
            lines.append("")
            lines.append("Concept Disagreements (Investigate):")
            for disagree in comparison['concept_disagreements'][:5]:
                lines.append(f"  {disagree['qname']}: {disagree['label']}")
        
        return "\n".join(lines)


__all__ = ['ComparisonReporter']