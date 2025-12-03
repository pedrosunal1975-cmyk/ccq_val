#!/usr/bin/env python3
"""
CCQ Mapper - Interactive Company Selector
==========================================

Interactive interface for CCQ mapper that discovers companies by scanning
parsed facts files and matching them with XBRL instances.

Uses the same path discovery logic as ParsedFactsLoader and XBRLLoader.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

# Suppress verbose logging
logging.basicConfig(level=logging.CRITICAL)
for logger_name in ['sqlalchemy', 'sqlalchemy.engine', 'sqlalchemy.engine.Engine',
                     'sqlalchemy.pool', 'core', 'engines', 'database']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    logging.getLogger(logger_name).propagate = False

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    from core.config_loader import ConfigLoader
    from core.data_paths import initialize_paths
    from engines.ccq_mapper import CCQMapperCoordinator
    from engines.ccq_mapper.loaders.parsed_facts_loader import ParsedFactsLoader
    from core.database_coordinator import DatabaseCoordinator
except ImportError as e:
    print(f"ERROR: Required packages not installed: {e}")
    print("Make sure you're running from the CCQ_VAL project directory")
    sys.exit(1)


class CompanyDiscovery:
    """
    Discovers available companies by scanning parsed facts files.
    
    Uses the same approach as ParsedFactsLoader - scans JSON files
    and extracts metadata directly from them.
    """
    
    def __init__(self, config: ConfigLoader):
        """
        Initialize company discovery.
        
        Args:
            config: Configuration loader
        """
        self.config = config
        self.parsed_facts_path = Path(config.get('parsed_facts_path'))
        self.xbrl_path = Path(config.get('mapper_xbrl_path'))
        
    def discover_companies(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Discover all available companies by scanning parsed facts files.
        
        Returns:
            Dictionary mapping market to list of company info dicts
        """
        companies_by_market = {}
        
        # Scan parsed facts directory for JSON files
        if not self.parsed_facts_path.exists():
            return companies_by_market
        
        # Scan all markets (sec, fca, esma)
        for market_dir in self.parsed_facts_path.iterdir():
            if not market_dir.is_dir():
                continue
            
            market = market_dir.name.lower()
            if market not in ['sec', 'fca', 'esma']:
                continue
            
            companies_by_market[market] = []
            
            # Scan for parsed facts JSON files recursively
            for json_file in market_dir.rglob('*.json'):
                company_info = self._extract_company_info(json_file, market)
                if company_info:
                    companies_by_market[market].append(company_info)
        
        # Sort companies alphabetically within each market
        for market in companies_by_market:
            companies_by_market[market].sort(key=lambda x: x['company_name'])
        
        return companies_by_market
    
    def _extract_company_info(
        self,
        json_file: Path,
        market: str
    ) -> Optional[Dict[str, str]]:
        """
        Extract company info from parsed facts JSON file.
        
        Args:
            json_file: Path to parsed facts JSON
            market: Market identifier
            
        Returns:
            Company info dict or None
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                return None
            
            metadata = data.get('metadata', {})
            if not metadata:
                return None
            
            filing_id = metadata.get('filing_id')
            company_name = metadata.get('company')
            form_type = metadata.get('filing_type')
            filing_date = metadata.get('filing_date')
            
            if not all([filing_id, company_name, form_type, filing_date]):
                return None
            
            # Find corresponding XBRL file
            xbrl_file = self._find_xbrl_file(json_file, market)
            
            return {
                'filing_id': filing_id,
                'company_name': company_name,
                'form_type': form_type,
                'filing_date': filing_date,
                'market': market,
                'parsed_facts_path': str(json_file),
                'xbrl_path': str(xbrl_file) if xbrl_file else None
            }
            
        except Exception:
            return None
    
    def _find_xbrl_file(
        self,
        parsed_facts_file: Path,
        market: str
    ) -> Optional[Path]:
        """
        Find XBRL instance file corresponding to parsed facts.
        
        MARKET-AGNOSTIC STRATEGY:
        Modern filings can be:
        - Traditional XBRL: company-date.xml
        - Inline XBRL (iXBRL): company-date.htm, .html, .xhtml
        - May have various naming patterns
        
        We need to find the INSTANCE DOCUMENT (not linkbases, not schemas).
        
        Strategy: Map from parsed_facts structure to entities structure
        /mnt/map_pro/data/parsed_facts/sec/company/form/date/file.json
        ->
        /mnt/map_pro/data/entities/sec/company/filings/form/accession/extracted/*
        
        Args:
            parsed_facts_file: Path to parsed facts JSON
            market: Market identifier
            
        Returns:
            Path to XBRL instance or None
        """
        try:
            # Extract path components
            parts = parsed_facts_file.parts
            market_idx = parts.index(market)
            
            company = parts[market_idx + 1]
            form_type = parts[market_idx + 2]
            filing_date = parts[market_idx + 3]
            
            # Search in entities directory
            company_dir = self.xbrl_path / market / company / 'filings' / form_type
            
            if not company_dir.exists():
                return None
            
            # Look for accession directories matching the filing date
            for accession_dir in company_dir.iterdir():
                if not accession_dir.is_dir():
                    continue
                
                extracted_dir = accession_dir / 'extracted'
                if not extracted_dir.exists():
                    continue
                
                # Find instance document - prioritize by likelihood
                instance_file = self._find_instance_document(extracted_dir)
                if instance_file:
                    return instance_file
            
            return None
            
        except Exception:
            return None
    
    def _find_instance_document(self, extracted_dir: Path) -> Optional[Path]:
        """
        Find the XBRL instance document in an extracted directory.
        
        Market-agnostic approach:
        1. Look for iXBRL (inline XBRL): .htm, .html, .xhtml files
        2. Look for traditional XBRL: .xml files
        3. Exclude linkbases (_lab, _pre, _cal, _def, _ref)
        4. Exclude schemas (.xsd)
        
        Priority: Primary form filing (10-K, 10-Q, etc.) over exhibits
        
        Args:
            extracted_dir: Directory with extracted files
            
        Returns:
            Path to instance document or None
        """
        candidates = []
        
        # Patterns to skip (not instance documents)
        skip_patterns = [
            '_lab.xml', '_pre.xml', '_cal.xml', '_def.xml', '_ref.xml',  # Linkbases
            '_lab.htm', '_pre.htm', '_cal.htm', '_def.htm', '_ref.htm',  # HTML linkbases
            '.xsd',  # Schemas
            '_htm.xml',  # Schema reference
            'xbrldi',  # XBRL dimension namespace
            'MetaLinks.json',  # Metadata
        ]
        
        # Check iXBRL files first (modern format) - .htm, .html, .xhtml
        for ext in ['.htm', '.html', '.xhtml']:
            for file in extracted_dir.glob(f'*{ext}'):
                filename = file.name
                
                # Skip if matches any skip pattern
                if any(pattern in filename for pattern in skip_patterns):
                    continue
                
                # Skip obvious exhibits (ex, xex in name)
                if 'xex' in filename.lower() or filename.startswith('ex'):
                    continue
                
                # Likely instance document
                candidates.append((file, 'ixbrl'))
        
        # Check traditional XBRL files (.xml)
        for file in extracted_dir.glob('*.xml'):
            filename = file.name
            
            # Skip if matches any skip pattern
            if any(pattern in filename for pattern in skip_patterns):
                continue
            
            # Likely instance document
            candidates.append((file, 'xbrl'))
        
        if not candidates:
            return None
        
        # Prioritize: iXBRL over traditional XBRL (more common in modern filings)
        # Then shortest filename (main filing vs exhibits)
        candidates.sort(key=lambda x: (0 if x[1] == 'ixbrl' else 1, len(x[0].name)))
        
        return candidates[0][0]
    

class DatabaseCleaner:
    """Cleans mapper database before each run."""
    
    def __init__(self):
        """Initialize database cleaner."""
        self.db = DatabaseCoordinator()
    
    def clean_for_filing(self, filing_id: str) -> bool:
        """
        Clean database records for a filing before mapping.
        
        Args:
            filing_id: Filing identifier to clean
            
        Returns:
            True if successful
        """
        try:
            from sqlalchemy import text
            
            with self.db.get_session() as session:
                # Delete from mapping_results
                session.execute(
                    text("DELETE FROM mapping_results WHERE filing_id = :filing_id"),
                    {"filing_id": filing_id}
                )
                
                # Delete from mapper_jobs
                session.execute(
                    text("DELETE FROM mapper_jobs WHERE filing_id = :filing_id"),
                    {"filing_id": filing_id}
                )
                
                session.commit()
            
            return True
            
        except Exception:
            return False


class CleanMapper:
    """Clean interface for CCQ mapper."""
    
    def __init__(self):
        """Initialize clean mapper."""
        self.config = ConfigLoader()
        self.discovery = CompanyDiscovery(self.config)
        self.cleaner = DatabaseCleaner()
        self.mapper = CCQMapperCoordinator()
    
    def run_interactive(self):
        """Run interactive company selection interface."""
        print("="*70)
        print("              CCQ MAPPER - Interactive Company Selector               ")
        print("="*70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Discover companies
        print("\n[SCAN] Scanning for available companies...")
        companies_by_market = self.discovery.discover_companies()
        
        if not companies_by_market or all(len(v) == 0 for v in companies_by_market.values()):
            print("ERROR: No companies found with complete XBRL and parsed facts data.")
            print("   Please check your data directories:")
            print(f"   Parsed Facts: {self.discovery.parsed_facts_path}")
            print(f"   XBRL Files:   {self.discovery.xbrl_path}")
            return
        
        # Display companies grouped by market
        print("\nAvailable companies:\n")
        
        selection_map = {}
        counter = 1
        
        for market in sorted(companies_by_market.keys()):
            companies = companies_by_market[market]
            if not companies:
                continue
            
            print(f"  {market.upper()} Market:")
            print("  " + "-"*66)
            
            for company in companies:
                print(f"  [{counter:2d}] {company['company_name']:<40} {company['form_type']:<8} {company['filing_date']}")
                selection_map[counter] = company
                counter += 1
            
            print()
        
        # Get user selection
        try:
            selection = input("Enter company number (or 'q' to quit): ").strip()
            
            if selection.lower() == 'q':
                print("\nExiting.")
                return
            
            selection_num = int(selection)
            
            if selection_num not in selection_map:
                print(f"\nERROR: Invalid selection: {selection_num}")
                return
            
            company = selection_map[selection_num]
            
        except ValueError:
            print("\nERROR: Invalid input. Please enter a number.")
            return
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            return
        
        # Run mapping
        print("\n" + "="*70)
        print(f"Mapping: {company['company_name']} - {company['form_type']} - {company['filing_date']}")
        print("="*70 + "\n")
        
        self._run_mapping(company)
    
    def _run_mapping(self, company: Dict[str, str]):
        """
        Run mapping for selected company.
        
        Args:
            company: Company info dictionary
        """
        filing_id = company['filing_id']
        parsed_facts_path = Path(company['parsed_facts_path'])
        xbrl_path = Path(company['xbrl_path']) if company['xbrl_path'] else None
        
        if not xbrl_path or not xbrl_path.exists():
            print(f"ERROR: XBRL file not found for {filing_id}")
            return
        
        # Clean database before mapping
        print("[CLEAN] Cleaning database...")
        self.cleaner.clean_for_filing(filing_id)
        
        # Get taxonomy paths
        taxonomy_paths = self._get_taxonomy_paths(company['market'])
        
        # Run mapping
        print("[MAP]  Running CCQ mapper...\n")
        
        result = self.mapper.map_filing(
            filing_id=filing_id,
            xbrl_path=xbrl_path,
            parsed_facts_path=parsed_facts_path,
            taxonomy_paths=taxonomy_paths
        )
        
        # Display results
        print("\n" + "="*70)
        if result.get('success'):
            print("SUCCESS: MAPPING COMPLETED SUCCESSFULLY")
            self._display_success_summary(result)
        else:
            print("ERROR: MAPPING FAILED")
            self._display_failure_summary(result)
        print("="*70)
    
    def _get_taxonomy_paths(self, market: str) -> List[Path]:
        """
        Get taxonomy paths for market.
        
        Args:
            market: Market identifier
            
        Returns:
            List of taxonomy paths
        """
        taxonomy_root = Path(self.config.get('taxonomy_path'))
        
        if not taxonomy_root.exists():
            return []
        
        # Find taxonomy directories for this market
        taxonomy_paths = []
        
        market_dir = taxonomy_root / market
        if market_dir.exists():
            for taxonomy_dir in market_dir.iterdir():
                if taxonomy_dir.is_dir():
                    taxonomy_paths.append(taxonomy_dir)
        
        return taxonomy_paths
    
    def _display_success_summary(self, result: Dict):
        """Display executive summary for successful mapping."""
        print("\n[SUMMARY] Executive Summary:")
        print("-" * 70)
        
        stats = result.get('statistics', {})
        success_metrics = result.get('success_metrics', {})
        duplicate_analysis = result.get('duplicate_analysis', {})
        gap_analysis = result.get('gap_analysis', {})
        statement_files = result.get('statement_files', [])
        
        print(f"  Filing ID:        {result.get('filing_id')}")
        
        # Total facts from source XBRL
        total = stats.get('total_facts', 0)
        print(f"  Total Facts (Source XBRL): {total:,}")
        
        # Processed facts (classified = looked at)
        classified = stats.get('classified_facts', 0)
        if total > 0:
            processed_pct = (classified / total) * 100
            print(f"  Processed Facts:  {classified:,} ({processed_pct:.1f}%)")
        else:
            print(f"  Processed Facts:  {classified:,}")
        
        # Duplicate facts with source attribution
        duplicate_count = 0
        if duplicate_analysis:
            dup_pct = duplicate_analysis.get('duplicate_percentage', 0)
            duplicate_count = duplicate_analysis.get('total_duplicate_facts', 0)
            duplicate_groups = duplicate_analysis.get('total_duplicate_groups', 0)
            
            # Show clearer breakdown
            if duplicate_groups > 0:
                avg_copies = duplicate_count / duplicate_groups
                print(f"  Duplicate Facts:  {duplicate_count:,} ({dup_pct:.1f}%) in {duplicate_groups:,} groups (avg {avg_copies:.1f} copies/group)")
            else:
                print(f"  Duplicate Facts:  {duplicate_count:,} ({dup_pct:.1f}%)")
            
            # Show source attribution if available
            source_attr = duplicate_analysis.get('source_attribution', {})
            if source_attr:
                source_data = source_attr.get('source_data', {})
                mapping_src = source_attr.get('mapping_introduced', {})
                unknown_src = source_attr.get('unknown', {})
                
                if source_data.get('facts', 0) > 0:
                    print(f"    - Source Data:  {source_data['facts']:,} ({source_data['percentage']:.1f}%)")
                if mapping_src.get('facts', 0) > 0:
                    print(f"    - Mapping:      {mapping_src['facts']:,} ({mapping_src['percentage']:.1f}%)")
                if unknown_src.get('facts', 0) > 0:
                    print(f"    - Unknown:      {unknown_src['facts']:,} ({unknown_src['percentage']:.1f}%)")
        
        # Classification gaps
        gap_count = 0
        if gap_analysis:
            gap_count = gap_analysis.get('gap_count', 0)
            gap_pct = gap_analysis.get('gap_percentage', 0)
            print(f"  Classification Gaps: {gap_count:,} ({gap_pct:.1f}%)")
        
        # Calculate successfully mapped facts
        unique_facts = total - duplicate_count
        mapped_facts = unique_facts - gap_count
        if total > 0:
            mapped_pct = (mapped_facts / total) * 100
            print(f"  Mapped Facts:     {mapped_facts:,} ({mapped_pct:.1f}%)")
        else:
            print(f"  Mapped Facts:     {mapped_facts:,}")
        
        # Show files written
        files_written = len(statement_files) if statement_files else stats.get('statements_constructed', 0)
        print(f"  Statement Files:  {files_written} written")
        
        # Overall success score
        if success_metrics:
            score = success_metrics.get('overall_score', 0)
            grade = success_metrics.get('success_level', 'UNKNOWN')
            print(f"  Overall Score:    {score:.1f}/100 ({grade})")
        
        # Null quality
        if stats.get('null_quality_score'):
            print(f"  Null Quality:     {stats.get('null_quality_score', 0):.1f}/100 ({stats.get('null_quality_grade', 'UNKNOWN')})")
        
        print()
    
    def _display_failure_summary(self, result: Dict):
        """Display error summary for failed mapping."""
        print("\nERROR: Error Details:")
        print("-" * 70)
        
        error = result.get('error', 'Unknown error')
        print(f"  {error}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CCQ Mapper - Interactive Company Selector"
    )
    
    args = parser.parse_args()
    
    try:
        mapper = CleanMapper()
        mapper.run_interactive()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()