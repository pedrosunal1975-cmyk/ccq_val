"""
Map Pro Error Analyzer
=======================

Location: ccq_val/engines/ccq_mapper/adapters/map_pro_analyzer.py

Analyzes parsing errors specific to Map Pro adapter.

Classes:
- MapProErrorAnalyzer: Analyzes Map Pro statement parsing errors
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import Counter

from .error_models import ErrorDetail, ErrorSummary
from .error_categorizer import (
    extract_namespace,
    categorize_error,
    check_missing_fields_map_pro
)
from .map_pro_adapter import MapProAdapter


class MapProErrorAnalyzer:
    """Analyzes parsing errors from Map Pro adapter."""
    
    def __init__(self):
        """Initialize analyzer with Map Pro adapter."""
        self.adapter = MapProAdapter()
    
    def analyze_statement(
        self,
        statement_path: Path,
        statement_type: str
    ) -> ErrorSummary:
        """
        Analyze Map Pro statement for parsing errors.
        
        Args:
            statement_path: Path to Map Pro statement JSON file
            statement_type: Type of statement (e.g., 'balance_sheet')
            
        Returns:
            ErrorSummary with detailed analysis
        """
        print(f"\n{'='*80}")
        print(f"Analyzing Map Pro: {statement_type}")
        print(f"{'='*80}")
        
        # Parse the statement
        neutral_facts = self.adapter.parse_statement_file(statement_path)
        stats = self.adapter.get_statistics()
        
        # Load raw data to get total count
        with open(statement_path, 'r') as f:
            raw_data = json.load(f)
        total_facts = len(raw_data.get('facts', []))
        
        # Calculate error rate
        error_rate = (
            stats['errors_count'] / total_facts * 100 
            if total_facts > 0 else 0
        )
        
        self._print_overview(total_facts, stats, error_rate)
        
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
            adapter_type='map_pro',
            total_facts=total_facts,
            successful_facts=stats['facts_processed'],
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
            fact = error_entry['fact']
            error_msg = error_entry['error']
            
            # Extract concept information
            concept = fact.get('concept', 'UNKNOWN')
            namespace = extract_namespace(concept)
            
            # Categorize error
            error_type = categorize_error(error_msg)
            
            # Check for missing fields
            missing = check_missing_fields_map_pro(fact)
            
            # Create detailed error record
            detail = ErrorDetail(
                error_type=error_type,
                error_message=error_msg,
                concept=concept,
                namespace=namespace,
                missing_fields=missing,
                has_value=bool(fact.get('value')),
                has_unit=bool(fact.get('unit')),
                has_context=bool(fact.get('context')),
                full_fact=fact
            )
            error_details.append(detail)
        
        return error_details
    
    def _print_overview(
        self,
        total_facts: int,
        stats: Dict,
        error_rate: float
    ):
        """Print overview of parsing results."""
        print(f"Total facts: {total_facts}")
        print(f"Successful: {stats['facts_processed']}")
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