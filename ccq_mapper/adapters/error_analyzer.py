"""
Enhanced Error Analyzer - Main Orchestrator
============================================

Location: ccq_val/engines/ccq_mapper/adapters/error_analyzer.py

Main orchestrator for analyzing adapter parsing errors.
This module coordinates the analysis workflow and maintains
backward compatibility with existing code.

Features:
- Orchestrates Map Pro and CCQ error analysis
- Generates comprehensive error reports
- Provides CLI interface for analysis

Usage:
    # Using environment variables (via .env)
    python -m engines.ccq_mapper.adapters.error_analyzer
    
    # Override via command line
    python -m engines.ccq_mapper.adapters.error_analyzer \
        --company PLUG_POWER_INC \
        --filing-date 2025-03-03 \
        --filing-type 10-K \
        --market sec

Components:
- error_models: Data structures for errors
- error_categorizer: Error classification utilities
- map_pro_analyzer: Map Pro error analysis
- ccq_analyzer: CCQ error analysis
- error_reporter: Report generation
"""

import sys
import argparse
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config_loader import ConfigLoader
from core.data_paths import CCQPaths

# Import refactored components
from .error_models import ErrorSummary
from .map_pro_analyzer import MapProErrorAnalyzer
from .ccq_analyzer import CCQErrorAnalyzer
from .error_reporter import ErrorReporter


class ErrorAnalyzer:
    """
    Main orchestrator for error analysis.
    
    Coordinates Map Pro and CCQ error analysis,
    maintains backward compatibility.
    """
    
    def __init__(self):
        """Initialize analyzer with component analyzers."""
        self.map_pro_analyzer = MapProErrorAnalyzer()
        self.ccq_analyzer = CCQErrorAnalyzer()
        self.reporter = ErrorReporter()
    
    def analyze_map_pro_errors(
        self,
        statement_path: Path,
        statement_type: str
    ) -> ErrorSummary:
        """
        Analyze Map Pro parsing errors.
        
        Args:
            statement_path: Path to Map Pro statement JSON
            statement_type: Type of statement
            
        Returns:
            ErrorSummary with detailed analysis
        """
        return self.map_pro_analyzer.analyze_statement(
            statement_path,
            statement_type
        )
    
    def analyze_ccq_errors(
        self,
        statement_path: Path,
        statement_type: str
    ) -> ErrorSummary:
        """
        Analyze CCQ parsing errors.
        
        Args:
            statement_path: Path to CCQ statement JSON
            statement_type: Type of statement
            
        Returns:
            ErrorSummary with detailed analysis
        """
        return self.ccq_analyzer.analyze_statement(
            statement_path,
            statement_type
        )
    
    def generate_report(
        self,
        summaries: List[ErrorSummary],
        output_path: Path
    ):
        """
        Generate comprehensive error report.
        
        Args:
            summaries: List of error summaries
            output_path: Path to save report
        """
        self.reporter.generate_report(summaries, output_path)
    
    def _calculate_overall_stats(self, summaries: List[ErrorSummary]):
        """Calculate overall statistics (delegates to reporter)."""
        return self.reporter._calculate_overall_stats(summaries)
    
    def _generate_recommendations(self, summaries: List[ErrorSummary]):
        """Generate recommendations (delegates to reporter)."""
        return self.reporter._generate_recommendations(summaries)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze adapter parsing errors for Map Pro and CCQ mappers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use defaults from .env file
  python -m engines.ccq_mapper.adapters.error_analyzer
  
  # Analyze specific filing
  python -m engines.ccq_mapper.adapters.error_analyzer \\
      --company PLUG_POWER_INC \\
      --filing-date 2025-03-03 \\
      --filing-type 10-K \\
      --market sec
  
  # Custom output location
  python -m engines.ccq_mapper.adapters.error_analyzer \\
      --output /custom/path/error_report.json
        """
    )
    
    parser.add_argument(
        '--company',
        type=str,
        help='Company name (e.g., PLUG_POWER_INC)'
    )
    
    parser.add_argument(
        '--filing-date',
        type=str,
        help='Filing date (e.g., 2025-03-03)'
    )
    
    parser.add_argument(
        '--filing-type',
        type=str,
        help='Filing type (e.g., 10-K, 10-Q, 8-K)'
    )
    
    parser.add_argument(
        '--market',
        type=str,
        default='sec',
        help='Market identifier (default: sec)'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        help='Output path for error report JSON'
    )
    
    parser.add_argument(
        '--statements',
        nargs='+',
        default=['balance_sheet', 'income_statement', 'cash_flow', 'other'],
        help='Statement types to analyze (default: all)'
    )
    
    return parser.parse_args()


def main():
    """Run error analysis using configuration-driven paths."""
    args = parse_arguments()
    
    print("\n" + "#"*80)
    print("# ENHANCED ERROR ANALYZER")
    print("# Detailed analysis of adapter parsing failures")
    print("#"*80)
    
    # Initialize configuration
    try:
        config = ConfigLoader()
        paths = CCQPaths.from_config(config)
    except Exception as e:
        print(f"\n❌ Error loading configuration: {e}")
        print("Make sure .env file exists and contains required paths")
        sys.exit(1)
    
    # Validate filing information
    if not (args.company and args.filing_date and args.filing_type):
        print(f"\n❌ Missing required arguments. Please provide:")
        print("  --company COMPANY_NAME")
        print("  --filing-date YYYY-MM-DD")
        print("  --filing-type FILING_TYPE")
        print("\nExample:")
        print("  python -m engines.ccq_mapper.adapters.error_analyzer \\")
        print("      --company PLUG_POWER_INC \\")
        print("      --filing-date 2025-03-03 \\")
        print("      --filing-type 10-K")
        sys.exit(1)
    
    company = args.company
    filing_date = args.filing_date
    filing_type = args.filing_type
    market = args.market
    
    print(f"\nAnalyzing filing:")
    print(f"  Company: {company}")
    print(f"  Filing Date: {filing_date}")
    print(f"  Filing Type: {filing_type}")
    print(f"  Market: {market}")
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        temp_dir = Path(config.get('temp_path', paths.data_root / 'temp_extractions'))
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_path = temp_dir / f'error_analysis_{company}_{filing_type}_{filing_date}.json'
    
    print(f"  Output: {output_path}\n")
    
    # Initialize analyzer and run analysis
    analyzer = ErrorAnalyzer()
    summaries = []
    
    for stmt in args.statements:
        # Map Pro path
        map_pro_path = (
            paths.input_mapped / market / company / 
            filing_type / filing_date / f"{stmt}.json"
        )
        
        # CCQ path
        ccq_path = paths.get_mapped_statement_path(
            market_type=market,
            entity_name=company,
            filing_type=filing_type,
            filing_date=filing_date,
            statement_type=stmt
        )
        
        # Analyze Map Pro
        if map_pro_path.exists():
            try:
                summary = analyzer.analyze_map_pro_errors(map_pro_path, stmt)
                summaries.append(summary)
            except Exception as e:
                print(f"❌ Error analyzing Map Pro {stmt}: {e}")
        else:
            print(f"⚠️  Map Pro {stmt} not found: {map_pro_path}")
        
        # Analyze CCQ
        if ccq_path and ccq_path.exists():
            try:
                summary = analyzer.analyze_ccq_errors(ccq_path, stmt)
                summaries.append(summary)
            except Exception as e:
                print(f"❌ Error analyzing CCQ {stmt}: {e}")
        else:
            print(f"⚠️  CCQ {stmt} not found: {ccq_path}")
    
    # Generate report
    if summaries:
        analyzer.generate_report(summaries, output_path)
        analyzer.reporter.print_summary(summaries)
    else:
        print("\n❌ No statements found to analyze")
        print(f"\nExpected paths:")
        print(f"  Map Pro: {paths.input_mapped}/{market}/{company}/{filing_type}/{filing_date}/")
        if paths.mapper_output:
            print(f"  CCQ: {paths.mapper_output}/{market}/{company}/{filing_type}/{filing_date}/")
    
    print(f"\n{'='*80}")
    print("Analysis complete!")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()