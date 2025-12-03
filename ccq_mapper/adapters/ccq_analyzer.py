"""
CCQ Error Analyzer
==================

Location: ccq_val/engines/ccq_mapper/adapters/ccq_analyzer.py

Analyzes parsing errors specific to CCQ adapter.

Classes:
- CCQErrorAnalyzer: Analyzes CCQ statement parsing errors
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import Counter

from .error_models import ErrorDetail, ErrorSummary
from .error_categorizer import (
    extract_namespace,
    categorize_error,
    check_missing_fields_ccq
)
from .ccq_adapter import CCQAdapter


class CCQErrorAnalyzer:
    """Analyzes parsing errors from CCQ adapter."""
    
    def __init__(self):
        """Initialize analyzer with CCQ adapter."""
        self.adapter = CCQAdapter()
    
    def analyze_statement(
        self,
        statement_path: Path,
        statement_type: str
    ) -> ErrorSummary:
        """
        Analyze CCQ statement for parsing errors.
        
        Args:
            statement_path: Path to CCQ statement JSON file
            statement_type: Type of statement (e.g., 'balance_sheet')
            
        Returns:
            ErrorSummary with detailed analysis
        """
        print(f"\n{'='*80}")
        print(f"Analyzing CCQ: {statement_type}")
        print(f"{'='*80}")
        
        # Parse the statement
        neutral_facts = self.adapter.parse_statement_file(statement_path)
        stats = self.adapter.get_statistics()
        
        # Load raw data to get total count
        with open(statement_path, 'r') as f:
            raw_data = json.load(f)
        total_items = len(raw_data.get('line_items', []))
        
        # Calculate error rate
        error_rate = (
            stats['errors_count'] / total_items * 100 
            if total_items > 0 else 0
        )
        
        self._print_overview(total_items, stats, error_rate)
        
        # Analyze errors in detail
        error_details = self._analyze_error_details(stats)
        
        # Collect statistics
        error_categories = Counter()
        missing_fields_freq = Counter()
        namespace_issues = Counter()
        
        for detail in error_details:
            error_categories[detail.error_type] += 1
            for field in detail.missing_fields:
                missing_fields_freq[field] += 1
            if detail.namespace:
                namespace_issues[detail.namespace] += 1
        
        # Print analysis results
        self._print_analysis_results(
            error_categories,
            missing_fields_freq,
            namespace_issues,
            error_details
        )
        
        return ErrorSummary(
            statement_type=statement_type,
            adapter_type='ccq',
            total_facts=total_items,
            successful_facts=stats['items_processed'],
            failed_facts=stats['errors_count'],
            error_rate=error_rate,
            error_categories=dict(error_categories),
            missing_fields_freq=dict(missing_fields_freq),
            problematic_namespaces=dict(namespace_issues),
            sample_errors=error_details[:10]
        )
    
    def _analyze_error_details(self, stats: Dict) -> List[ErrorDetail]:
        """
        Analyze individual error entries.
        
        Args:
            stats: Statistics dictionary from adapter
            
        Returns:
            List of ErrorDetail objects
        """
        error_details = []
        
        for error_entry in stats['errors']:
            item = error_entry['item']
            error_msg = error_entry['error']
            
            # Extract concept information
            qname = item.get('qname', 'UNKNOWN')
            namespace = extract_namespace(qname)
            
            # Categorize error
            error_type = categorize_error(error_msg)
            
            # Check for missing fields
            missing = check_missing_fields_ccq(item)
            
            # Create detailed error record
            detail = ErrorDetail(
                error_type=error_type,
                error_message=error_msg,
                concept=qname,
                namespace=namespace,
                missing_fields=missing,
                has_value=bool(item.get('value')),
                has_unit=bool(item.get('unit')),
                has_context=bool(item.get('context_ref')),
                full_fact=item
            )
            error_details.append(detail)
        
        return error_details
    
    def _print_overview(
        self,
        total_items: int,
        stats: Dict,
        error_rate: float
    ):
        """Print overview of parsing results."""
        print(f"Total items: {total_items}")
        print(f"Successful: {stats['items_processed']}")
        print(f"Failed: {stats['errors_count']}")
        print(f"Error rate: {error_rate:.1f}%")
    
    def _print_analysis_results(
        self,
        error_categories: Counter,
        missing_fields_freq: Counter,
        namespace_issues: Counter,
        error_details: List[ErrorDetail]
    ):
        """Print detailed analysis results."""
        print(f"\nError Categories:")
        for category, count in error_categories.most_common():
            print(f"  {category}: {count}")
        
        if missing_fields_freq:
            print(f"\nMissing Fields Frequency:")
            for field, count in missing_fields_freq.most_common():
                print(f"  {field}: {count}")
        
        if namespace_issues:
            print(f"\nProblematic Namespaces:")
            for ns, count in namespace_issues.most_common(10):
                print(f"  {ns}: {count}")
        
        print(f"\nSample Errors (first 3):")
        for i, detail in enumerate(error_details[:3], 1):
            print(f"\n  Error {i}:")
            print(f"    Type: {detail.error_type}")
            print(f"    Concept: {detail.concept}")
            print(f"    Namespace: {detail.namespace}")
            print(f"    Missing: {detail.missing_fields}")
            print(f"    Message: {detail.error_message[:100]}...")