"""
Financial Statement Comparator
===============================

Specialized comparator for financial statements:
- Balance Sheet
- Income Statement
- Cash Flow Statement
- Other

Handles all financial statement comparison logic.
"""

from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict

from core.system_logger import get_logger
from core.data_paths import CCQPaths

from .comparison_engine import ComparisonEngine

logger = get_logger(__name__)


class FinancialStatementComparator:
    """
    Comparator for financial statements.
    
    Handles balance sheet, income statement, cash flow, and other comparisons.
    """
    
    def __init__(self, paths: CCQPaths):
        """Initialize with CCQPaths instance."""
        self.paths = paths
        self.engine = ComparisonEngine(paths)
    
    # ========================================================================
    # PUBLIC API - Individual Statement Comparisons
    # ========================================================================
    
    def compare_balance_sheets(
        self,
        market: str,
        company: str,
        form_type: str,
        filing_date: str,
        filter_instant_only: bool = True
    ) -> Dict[str, Any]:
        """Compare balance sheets from Map Pro and CCQ Mapper."""
        logger.info(f"Comparing balance sheets for {company} {form_type} {filing_date}")
        if filter_instant_only:
            logger.info("Filter: instant items only (balance sheet should be point-in-time)")
        
        return self._compare_statement(
            market, company, form_type, filing_date,
            filename='balance_sheet.json',
            statement_type='balance_sheet',
            filter_instant_only=filter_instant_only,
            filter_duration_only=False
        )
    
    def compare_income_statements(
        self,
        market: str,
        company: str,
        form_type: str,
        filing_date: str,
        filter_duration_only: bool = True
    ) -> Dict[str, Any]:
        """Compare income statements from Map Pro and CCQ Mapper."""
        logger.info(f"Comparing income statements for {company} {form_type} {filing_date}")
        if filter_duration_only:
            logger.info("Filter: duration items only (income statement should be period-based)")
        
        return self._compare_statement(
            market, company, form_type, filing_date,
            filename='income_statement.json',
            statement_type='income_statement',
            filter_instant_only=False,
            filter_duration_only=filter_duration_only
        )
    
    def compare_cash_flows(
        self,
        market: str,
        company: str,
        form_type: str,
        filing_date: str,
        filter_duration_only: bool = True
    ) -> Dict[str, Any]:
        """Compare cash flow statements from Map Pro and CCQ Mapper."""
        logger.info(f"Comparing cash flow statements for {company} {form_type} {filing_date}")
        if filter_duration_only:
            logger.info("Filter: duration items only (cash flow should be period-based)")
        
        return self._compare_statement(
            market, company, form_type, filing_date,
            filename='cash_flow.json',
            statement_type='cash_flow',
            filter_instant_only=False,
            filter_duration_only=filter_duration_only
        )
    
    def compare_other(
        self,
        market: str,
        company: str,
        form_type: str,
        filing_date: str
    ) -> Dict[str, Any]:
        """Compare 'other' statements from Map Pro and CCQ Mapper."""
        logger.info(f"Comparing 'other' statements for {company} {form_type} {filing_date}")
        logger.info("No period_type filtering (other contains mixed types)")
        
        return self._compare_statement(
            market, company, form_type, filing_date,
            filename='other.json',
            statement_type='other',
            filter_instant_only=False,
            filter_duration_only=False
        )
    
    # ========================================================================
    # PRIVATE - Core Comparison Logic
    # ========================================================================
    
    def _compare_statement(
        self,
        market: str,
        company: str,
        form_type: str,
        filing_date: str,
        filename: str,
        statement_type: str,
        filter_instant_only: bool = False,
        filter_duration_only: bool = False
    ) -> Dict[str, Any]:
        """
        Core statement comparison logic.
        
        Used by all financial statement comparison methods.
        """
        # Find files
        map_pro_file = self.engine.find_statement_file(
            self.paths.input_mapped, market, company, form_type, filing_date, filename
        )
        
        ccq_file = self.engine.find_statement_file(
            self.paths.mapper_output, market, company, form_type, filing_date, filename
        )
        
        # Check if files exist
        if not map_pro_file:
            return {
                'success': False,
                'error': f'Map Pro {statement_type} not found for {company} {form_type} {filing_date}',
                'searched_in': str(self.paths.input_mapped)
            }
        
        if not ccq_file:
            return {
                'success': False,
                'error': f'CCQ {statement_type} not found for {company} {form_type} {filing_date}',
                'searched_in': str(self.paths.mapper_output)
            }
        
        logger.info(f"✓ Found Map Pro file: {map_pro_file}")
        logger.info(f"✓ Found CCQ file: {ccq_file}")
        
        # Load statements
        try:
            map_pro_stmt = self.engine.load_statement(map_pro_file)
            ccq_stmt = self.engine.load_statement(ccq_file)
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to load statements: {e}'
            }
        
        # Perform comparison
        comparison = self._compare_line_items(
            map_pro_stmt, 
            ccq_stmt, 
            statement_type,
            filter_instant_only=filter_instant_only,
            filter_duration_only=filter_duration_only
        )
        
        # Add metadata
        comparison['files'] = {
            'map_pro': str(map_pro_file),
            'ccq': str(ccq_file)
        }
        comparison['compared_at'] = datetime.now().isoformat()
        comparison['filter_instant_only'] = filter_instant_only
        comparison['filter_duration_only'] = filter_duration_only
        
        return comparison
    
    def _compare_line_items(
        self,
        map_pro_stmt: Dict[str, Any],
        ccq_stmt: Dict[str, Any],
        stmt_type: str,
        filter_instant_only: bool = False,
        filter_duration_only: bool = False
    ) -> Dict[str, Any]:
        """Compare line items from two statements."""
        logger.info("Performing detailed comparison...")
        
        # Extract line items
        map_pro_items_raw = self.engine.extract_line_items(map_pro_stmt)
        ccq_items_raw = self.engine.extract_line_items(ccq_stmt)
        
        logger.info(f"Before filtering - Map Pro: {len(map_pro_items_raw)}, CCQ: {len(ccq_items_raw)}")
        
        # Apply filters
        if filter_instant_only:
            map_pro_items_raw = [item for item in map_pro_items_raw if self.engine.is_instant_item(item)]
            ccq_items_raw = [item for item in ccq_items_raw if self.engine.is_instant_item(item)]
            logger.info(f"After instant filter - Map Pro: {len(map_pro_items_raw)}, CCQ: {len(ccq_items_raw)}")
        
        if filter_duration_only:
            map_pro_items_raw = [item for item in map_pro_items_raw if self.engine.is_duration_item(item)]
            ccq_items_raw = [item for item in ccq_items_raw if self.engine.is_duration_item(item)]
            logger.info(f"After duration filter - Map Pro: {len(map_pro_items_raw)}, CCQ: {len(ccq_items_raw)}")
        
        # Normalize items
        map_pro_items = [self.engine.normalize_line_item(item) for item in map_pro_items_raw]
        ccq_items = [self.engine.normalize_line_item(item) for item in ccq_items_raw]
        
        logger.info(f"Map Pro: {len(map_pro_items)} line items")
        logger.info(f"CCQ: {len(ccq_items)} line items")
        
        # Build concept indexes
        map_pro_by_qname = {
            item['qname']: item 
            for item in map_pro_items 
            if item.get('qname')
        }
        
        ccq_by_qname = {}
        for item in ccq_items:
            qname = item.get('qname')
            if not qname:
                continue
            
            if qname not in ccq_by_qname:
                ccq_by_qname[qname] = []
            ccq_by_qname[qname].append(item)
        
        logger.info(f"Map Pro unique concepts: {len(map_pro_by_qname)}")
        logger.info(f"CCQ unique concepts: {len(ccq_by_qname)}")
        
        # Find matches and mismatches
        all_qnames = set(map_pro_by_qname.keys()) | set(ccq_by_qname.keys())
        
        matches = []
        value_mismatches = []
        map_pro_only = []
        ccq_only = []
        
        for qname in sorted(all_qnames):
            map_pro_item = map_pro_by_qname.get(qname)
            ccq_items_for_qname = ccq_by_qname.get(qname, [])
            
            if map_pro_item and ccq_items_for_qname:
                comparison = self._compare_concept_with_instances(map_pro_item, ccq_items_for_qname)
                
                if comparison['values_match']:
                    matches.append(comparison)
                else:
                    value_mismatches.append(comparison)
            
            elif map_pro_item and not ccq_items_for_qname:
                map_pro_only.append({
                    'qname': qname,
                    'label': map_pro_item.get('label'),
                    'value': map_pro_item.get('value'),
                    'context': map_pro_item.get('context_ref') or map_pro_item.get('context')
                })
            
            elif ccq_items_for_qname and not map_pro_item:
                ccq_first = ccq_items_for_qname[0]
                ccq_only.append({
                    'qname': qname,
                    'label': ccq_first.get('label'),
                    'value': ccq_first.get('value'),
                    'context': ccq_first.get('context_ref'),
                    'ccq_instance_count': len(ccq_items_for_qname)
                })
        
        # Calculate statistics
        total_concepts = len(all_qnames)
        matched_concepts = len(matches)
        agreement_rate = (matched_concepts / total_concepts * 100) if total_concepts > 0 else 0
        
        # Build report
        return {
            'success': True,
            'statement_type': stmt_type,
            'summary': {
                'total_concepts': total_concepts,
                'matched_concepts': matched_concepts,
                'value_mismatches': len(value_mismatches),
                'map_pro_only_concepts': len(map_pro_only),
                'ccq_only_concepts': len(ccq_only),
                'agreement_rate': round(agreement_rate, 2)
            },
            'matches': matches[:10],
            'value_mismatches': value_mismatches,
            'map_pro_only': map_pro_only,
            'ccq_only': ccq_only,
            'total_matches': len(matches),
            'metadata': {
                'map_pro': self.engine.extract_statement_metadata(map_pro_stmt),
                'ccq': self.engine.extract_statement_metadata(ccq_stmt)
            }
        }
    
    def _compare_concept_with_instances(
        self,
        map_pro_item: Dict[str, Any],
        ccq_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare Map Pro's single value against CCQ's multiple instances."""
        qname = map_pro_item.get('qname')
        map_pro_value = self.engine.normalize_value(map_pro_item.get('value'))
        
        ccq_values = [self.engine.normalize_value(item.get('value')) for item in ccq_items]
        
        values_match = any(
            self.engine.values_equal(map_pro_value, ccq_val) 
            for ccq_val in ccq_values
        )
        
        comparison = {
            'qname': qname,
            'label': {
                'map_pro': map_pro_item.get('label'),
                'ccq': ccq_items[0].get('label') if ccq_items else None
            },
            'value': {
                'map_pro': map_pro_value,
                'ccq': ccq_values[0] if ccq_values else None,
                'ccq_all_values': ccq_values if len(ccq_values) > 1 else None
            },
            'values_match': values_match,
            'ccq_instance_count': len(ccq_items),
            'context': {
                'map_pro': map_pro_item.get('context_ref') or map_pro_item.get('context'),
                'ccq': [item.get('context_ref') for item in ccq_items]
            }
        }
        
        if values_match:
            for i, ccq_val in enumerate(ccq_values):
                if self.engine.values_equal(map_pro_value, ccq_val):
                    comparison['matched_ccq_index'] = i
                    comparison['matched_ccq_context'] = ccq_items[i].get('context_ref')
                    break
        else:
            if map_pro_value is not None and ccq_values and ccq_values[0] is not None:
                try:
                    mp_num = float(map_pro_value)
                    ccq_num = float(ccq_values[0])
                    comparison['difference'] = ccq_num - mp_num
                    comparison['percent_difference'] = ((ccq_num - mp_num) / mp_num * 100) if mp_num != 0 else None
                except (ValueError, TypeError):
                    comparison['difference'] = 'N/A (non-numeric)'
        
        return comparison
    
    # ========================================================================
    # PUBLIC API - Reporting
    # ========================================================================
    
    def print_financial_report(self, comparison: Dict[str, Any]):
        """Print a human-readable financial statement comparison report."""
        summary = comparison['summary']
        stmt_type = comparison.get('statement_type', 'statement').replace('_', ' ').title()
        
        print("\n" + "="*80)
        print(f"{stmt_type.upper()} COMPARISON REPORT")
        print("="*80)
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total concepts: {summary['total_concepts']}")
        print(f"  Matched concepts: {summary['matched_concepts']}")
        print(f"  Agreement rate: {summary['agreement_rate']}%")
        print(f"  Value mismatches: {summary['value_mismatches']}")
        print(f"  Map Pro only: {summary['map_pro_only_concepts']}")
        print(f"  CCQ only: {summary['ccq_only_concepts']}")
        
        # Value mismatches
        if comparison['value_mismatches']:
            print(f"\n⚠️  VALUE MISMATCHES ({len(comparison['value_mismatches'])}):")
            for mismatch in comparison['value_mismatches'][:10]:
                print(f"\n  Concept: {mismatch['qname']}")
                print(f"    Label: {mismatch['label']['map_pro']}")
                print(f"    Map Pro value: {mismatch['value']['map_pro']}")
                print(f"    CCQ value: {mismatch['value']['ccq']}")
                if 'difference' in mismatch:
                    print(f"    Difference: {mismatch['difference']}")
            
            if len(comparison['value_mismatches']) > 10:
                print(f"\n  ... and {len(comparison['value_mismatches']) - 10} more")
        
        # Map Pro only
        if comparison['map_pro_only']:
            print(f"\n📌 MAP PRO ONLY ({len(comparison['map_pro_only'])}):")
            for item in comparison['map_pro_only'][:10]:
                print(f"  - {item['qname']}: {item['label']} = {item['value']}")
            
            if len(comparison['map_pro_only']) > 10:
                print(f"  ... and {len(comparison['map_pro_only']) - 10} more")
        
        # CCQ only
        if comparison['ccq_only']:
            print(f"\n📌 CCQ ONLY ({len(comparison['ccq_only'])}):")
            for item in comparison['ccq_only'][:10]:
                print(f"  - {item['qname']}: {item['label']} = {item['value']}")
            
            if len(comparison['ccq_only']) > 10:
                print(f"  ... and {len(comparison['ccq_only']) - 10} more")
        
        # Sample matches
        if comparison.get('total_matches', 0) > 0:
            print(f"\n✓ SAMPLE MATCHES (showing 5 of {comparison['total_matches']}):")
            for match in comparison['matches'][:5]:
                print(f"  - {match['qname']}: {match['value']['map_pro']} (both agree)")
        
        print("\n" + "="*80)


__all__ = ['FinancialStatementComparator']