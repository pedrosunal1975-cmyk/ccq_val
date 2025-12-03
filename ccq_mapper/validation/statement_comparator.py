"""
Statement Comparator
====================

Main coordinator for comparing Map Pro and CCQ Mapper outputs.
Delegates to specialized comparison engines.

Uses CCQPaths for robust file location - ALL paths from .env configuration.
"""

from typing import Dict, Any
from pathlib import Path
from datetime import datetime

from core.system_logger import get_logger
from core.config_loader import ConfigLoader
from core.data_paths import CCQPaths

from .financial_statement_comparator import FinancialStatementComparator
from .quality_report_comparator import QualityReportComparator

logger = get_logger(__name__)


class StatementComparator:
    """
    Main coordinator for statement comparisons.
    
    Provides a unified interface for comparing:
    - Financial statements (balance sheet, income, cash flow, other)
    - Quality reports (null quality)
    
    Delegates actual comparison work to specialized engines.
    """
    
    def __init__(self):
        """Initialize comparator with paths from .env config."""
        self.config = ConfigLoader()
        
        # Initialize CCQPaths - all paths from .env
        self.paths = CCQPaths(
            data_root=self.config.get('data_root'),
            input_path=self.config.get('input_path'),
            output_path=self.config.get('output_path'),
            taxonomy_path=self.config.get('taxonomy_path'),
            parsed_facts_path=self.config.get('parsed_facts_path'),
            mapper_xbrl_path=self.config.get('mapper_xbrl_path'),
            mapper_output_path=self.config.get('mapper_output_path'),
            ccq_logs_path=self.config.get('ccq_logs_path'),
            mapper_logs_path=self.config.get('mapper_logs_path')
        )
        
        # Initialize specialized comparators
        self.financial_comparator = FinancialStatementComparator(self.paths)
        self.quality_comparator = QualityReportComparator(self.paths)
        
        logger.info(f"Map Pro statements path: {self.paths.input_mapped}")
        logger.info(f"CCQ mapped statements path: {self.paths.mapper_output}")
    
    # ========================================================================
    # PUBLIC API - Financial Statements
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
        return self.financial_comparator.compare_balance_sheets(
            market, company, form_type, filing_date, filter_instant_only
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
        return self.financial_comparator.compare_income_statements(
            market, company, form_type, filing_date, filter_duration_only
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
        return self.financial_comparator.compare_cash_flows(
            market, company, form_type, filing_date, filter_duration_only
        )
    
    def compare_other(
        self,
        market: str,
        company: str,
        form_type: str,
        filing_date: str
    ) -> Dict[str, Any]:
        """Compare 'other' statements from Map Pro and CCQ Mapper."""
        return self.financial_comparator.compare_other(
            market, company, form_type, filing_date
        )
    
    # ========================================================================
    # PUBLIC API - Quality Reports
    # ========================================================================
    
    def compare_null_quality(
        self,
        market: str,
        company: str,
        form_type: str,
        filing_date: str
    ) -> Dict[str, Any]:
        """Compare null quality reports from Map Pro and CCQ Mapper."""
        return self.quality_comparator.compare_null_quality(
            market, company, form_type, filing_date
        )
    
    # ========================================================================
    # PUBLIC API - Combined Comparisons
    # ========================================================================
    
    def compare_all_statements(
        self,
        market: str,
        company: str,
        form_type: str,
        filing_date: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare ALL statement types between Map Pro and CCQ Mapper.
        
        Returns combined report for all statements.
        """
        logger.info(f"Running comprehensive comparison for {company} {form_type} {filing_date}")
        
        results = {
            'balance_sheet': self.compare_balance_sheets(market, company, form_type, filing_date),
            'income_statement': self.compare_income_statements(market, company, form_type, filing_date),
            'cash_flow': self.compare_cash_flows(market, company, form_type, filing_date),
            'other': self.compare_other(market, company, form_type, filing_date),
            'null_quality': self.compare_null_quality(market, company, form_type, filing_date)
        }
        
        # Calculate overall statistics
        overall_summary = {
            'total_comparisons': len(results),
            'successful_comparisons': sum(1 for r in results.values() if r.get('success')),
            'failed_comparisons': sum(1 for r in results.values() if not r.get('success')),
            'average_agreement_rate': self._calculate_average_agreement(results),
            'compared_at': datetime.now().isoformat()
        }
        
        results['overall_summary'] = overall_summary
        
        return results
    
    # ========================================================================
    # PUBLIC API - Reporting
    # ========================================================================
    
    def print_comparison_report(self, comparison: Dict[str, Any]):
        """Print a human-readable comparison report."""
        if not comparison.get('success'):
            print(f"\n✗ Comparison failed: {comparison.get('error')}")
            if 'searched_in' in comparison:
                print(f"   Searched in: {comparison['searched_in']}")
            return
        
        # Delegate to appropriate reporter
        report_type = comparison.get('report_type', 'financial_statement')
        
        if report_type == 'null_quality':
            self.quality_comparator.print_quality_report(comparison)
        else:
            self.financial_comparator.print_financial_report(comparison)
    
    def save_comparison_report(self, comparison: Dict[str, Any], output_path: Path):
        """Save comparison report to JSON file."""
        import json
        
        logger.info(f"Saving comparison report to: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, default=str)
        
        logger.info(f"✓ Saved comparison report")
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _calculate_average_agreement(self, results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate average agreement rate across all successful comparisons."""
        agreement_rates = []
        
        for stmt_type, result in results.items():
            if stmt_type == 'overall_summary':
                continue
            
            if result.get('success') and 'summary' in result:
                rate = result['summary'].get('agreement_rate')
                if rate is not None:
                    agreement_rates.append(rate)
        
        if not agreement_rates:
            return 0.0
        
        return round(sum(agreement_rates) / len(agreement_rates), 2)


__all__ = ['StatementComparator']