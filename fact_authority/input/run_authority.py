# File: engines/fact_authority/input/run_authority.py
# Path: engines/fact_authority/input/run_authority.py

"""
Fact Authority - Interactive Company Selector
==============================================

Interactive CLI interface for fact_authority engine.

Discovers companies with mapped statements in BOTH Map Pro and CCQ,
allows user to select a filing, then validates against taxonomy authority.

Usage:
    python -m engines.fact_authority.input.run_authority
    
Or from project root:
    python engines/fact_authority/input/run_authority.py
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from core.config_loader import ConfigLoader
from core.data_paths import CCQPaths
from core.name_normalizer import NameNormalizer
from core.system_logger import get_logger
from engines.fact_authority.fact_authority import FactAuthority

logger = get_logger(__name__)


class FilingDiscovery:
    """
    Discovers filings available in BOTH Map Pro and CCQ outputs.
    
    Scans both mapper output directories and finds intersection using fuzzy matching.
    """
    
    def __init__(self, ccq_paths: CCQPaths):
        """
        Initialize discovery with CCQPaths.
        
        Args:
            ccq_paths: CCQPaths instance
        """
        self.ccq_paths = ccq_paths
        self.map_pro_path = ccq_paths.input_mapped
        self.ccq_path = ccq_paths.mapper_output
        self.normalizer = NameNormalizer()
    
    def discover_filings(self) -> List[Dict[str, str]]:
        """
        Discover filings in BOTH Map Pro and CCQ outputs.
        
        Returns:
            List of filing dicts with keys:
                - market
                - entity_name (from Map Pro)
                - ccq_entity_name (from CCQ, if different) - for display only
                - filing_type
                - filing_date
                - display_name
        """
        print(f"\nScanning Map Pro outputs: {self.map_pro_path}")
        print(f"Scanning CCQ outputs: {self.ccq_path}\n")
        
        # Scan both directories
        map_pro_filings = self._scan_directory(self.map_pro_path)
        ccq_filings = self._scan_directory(self.ccq_path)
        
        # Find intersection with fuzzy matching
        return self._find_intersection_fuzzy(map_pro_filings, ccq_filings)
    
    def _scan_directory(self, base_path: Path) -> Dict[str, Dict]:
        """
        Scan mapper output directory for filings.
        
        Args:
            base_path: Base directory to scan
            
        Returns:
            Dict mapping filing_key to filing_info
        """
        filings = {}
        
        if not base_path.exists():
            logger.warning(f"Directory does not exist: {base_path}")
            return filings
        
        # Structure: market/entity/filing_type/date/
        for market_dir in base_path.iterdir():
            if not market_dir.is_dir():
                continue
            
            market = market_dir.name
            
            for entity_dir in market_dir.iterdir():
                if not entity_dir.is_dir():
                    continue
                
                entity_name = entity_dir.name
                
                for filing_type_dir in entity_dir.iterdir():
                    if not filing_type_dir.is_dir():
                        continue
                    
                    filing_type = filing_type_dir.name
                    
                    for date_dir in filing_type_dir.iterdir():
                        if not date_dir.is_dir():
                            continue
                        
                        filing_date = date_dir.name
                        
                        # Check if this directory has statement files
                        statement_files = list(date_dir.glob('*.json'))
                        if not statement_files:
                            continue
                        
                        # Create unique key with normalized entity name for matching
                        normalized_entity = self.normalizer.normalize_for_comparison(entity_name)
                        filing_key = f"{market}/{normalized_entity}/{filing_type}/{filing_date}"
                        
                        filings[filing_key] = {
                            'market': market,
                            'entity_name': entity_name,  # Keep original name
                            'normalized_entity': normalized_entity,
                            'filing_type': filing_type,
                            'filing_date': filing_date,
                            'display_name': self._format_display_name(
                                entity_name, filing_type, filing_date
                            )
                        }
        
        return filings
    
    def _find_intersection_fuzzy(
        self,
        map_pro_filings: Dict[str, Dict],
        ccq_filings: Dict[str, Dict]
    ) -> List[Dict[str, str]]:
        """
        Find filings present in BOTH Map Pro and CCQ using fuzzy name matching.
        
        Args:
            map_pro_filings: Map Pro filings dict (keyed by normalized names)
            ccq_filings: CCQ filings dict (keyed by normalized names)
            
        Returns:
            List of filing info dicts
        """
        # Keys are already normalized, so we can do direct set intersection
        common_keys = set(map_pro_filings.keys()) & set(ccq_filings.keys())
        
        common_filings = []
        
        for key in sorted(common_keys):
            map_pro_filing = map_pro_filings[key]
            ccq_filing = ccq_filings[key]
            
            # Use Map Pro's entity name as primary, but note if CCQ differs
            filing_info = {
                'market': map_pro_filing['market'],
                'entity_name': map_pro_filing['entity_name'],  # Map Pro name
                'filing_type': map_pro_filing['filing_type'],
                'filing_date': map_pro_filing['filing_date'],
                'display_name': map_pro_filing['display_name']
            }
            
            # Track if CCQ uses different name (for display purposes only)
            if map_pro_filing['entity_name'] != ccq_filing['entity_name']:
                filing_info['ccq_entity_name'] = ccq_filing['entity_name']
                filing_info['name_mismatch'] = True
                logger.info(
                    f"Name variation detected - Map Pro: {map_pro_filing['entity_name']}, "
                    f"CCQ: {ccq_filing['entity_name']}"
                )
            
            common_filings.append(filing_info)
        
        print(f"Found {len(map_pro_filings)} Map Pro filings")
        print(f"Found {len(ccq_filings)} CCQ filings")
        print(f"Found {len(common_filings)} filings in BOTH mappers (using fuzzy matching)\n")
        
        return common_filings
    
    def _format_display_name(
        self,
        entity_name: str,
        filing_type: str,
        filing_date: str
    ) -> str:
        """
        Format display name for filing.
        
        Args:
            entity_name: Entity name (with underscores)
            filing_type: Filing type
            filing_date: Filing date
            
        Returns:
            Formatted display name
        """
        # Replace underscores with spaces and remove trailing punctuation
        readable_name = entity_name.replace('_', ' ').strip('._')
        
        # Remove common suffixes
        readable_name = readable_name.replace(' Inc', '')
        readable_name = readable_name.replace(' LLC', '')
        readable_name = readable_name.replace(' Ltd', '')
        
        return f"{readable_name} ({filing_type}, {filing_date})"


def display_menu(filings: List[Dict[str, str]]) -> None:
    """
    Display filing selection menu.
    
    Args:
        filings: List of filing dicts
    """
    print("=" * 80)
    print("FACT AUTHORITY - TAXONOMY VALIDATION ENGINE")
    print("=" * 80)
    print("\nAvailable filings for validation:\n")
    
    for idx, filing in enumerate(filings, 1):
        display = filing['display_name']
        
        # Show if there's a name mismatch between systems
        if filing.get('name_mismatch'):
            display += f" [CCQ: {filing['ccq_entity_name']}]"
        
        print(f"  {idx}. {display}")
    
    print(f"\n  q. Quit")
    print("=" * 80)


def get_user_selection(filings: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Get user's filing selection.
    
    Args:
        filings: List of filing dicts
        
    Returns:
        Selected filing dict, or None if user quits
    """
    while True:
        try:
            user_input = input("\nEnter selection (1-{}) or 'q' to quit: ".format(
                len(filings)
            )).strip().lower()
            
            if user_input == 'q':
                return None
            
            selection = int(user_input)
            
            if 1 <= selection <= len(filings):
                return filings[selection - 1]
            else:
                print(f"Invalid selection. Please enter 1-{len(filings)} or 'q'")
                
        except ValueError:
            print("Invalid input. Please enter a number or 'q'")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return None


def run_validation(filing: Dict[str, str], ccq_paths: CCQPaths) -> bool:
    """
    Run validation on selected filing.
    
    Name variations between Map Pro and CCQ are handled automatically
    by statement_loader and duplicate_report_loader using NameNormalizer.
    
    Args:
        filing: Filing info dict
        ccq_paths: CCQPaths instance
        
    Returns:
        True if validation succeeded, False otherwise
    """
    print("\n" + "=" * 80)
    print(f"VALIDATING: {filing['display_name']}")
    print("=" * 80)
    print(f"\nMarket: {filing['market']}")
    print(f"Entity: {filing['entity_name']}")
    print(f"Filing Type: {filing['filing_type']}")
    print(f"Filing Date: {filing['filing_date']}")
    
    if filing.get('name_mismatch'):
        print(f"Note: CCQ uses name '{filing['ccq_entity_name']}' (handled automatically)")
    
    print()
    
    try:
        # Initialize fact authority
        fact_authority = FactAuthority(ccq_paths)
        
        # Run validation
        # Note: Name variations are handled automatically by loaders
        result = fact_authority.validate_filing(
            market=filing['market'],
            entity_name=filing['entity_name'],
            filing_type=filing['filing_type'],
            filing_date=filing['filing_date'],
            write_output=True
        )
        
        # Display results
        print("\n" + "=" * 80)
        if result['success']:
            print("VALIDATION COMPLETED SUCCESSFULLY")
            print("=" * 80)
            
            if 'statistics' in result:
                stats = result['statistics']
                print("\nValidation Statistics:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            
            if 'output_path' in result:
                print(f"\nValidated statements written to:")
                print(f"  {result['output_path']}")
            
            return True
        else:
            print("VALIDATION FAILED")
            print("=" * 80)
            
            if 'errors' in result:
                print("\nErrors:")
                for error in result['errors']:
                    print(f"  - {error}")
            
            if 'phase' in result:
                print(f"\nFailed in phase: {result['phase']}")
            
            return False
            
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        logger.error(f"Fatal error during validation: {e}", exc_info=True)
        return False


def main():
    """Main entry point for interactive fact authority validation."""
    print("\nInitializing Fact Authority Engine...")
    
    try:
        # Load configuration
        config_loader = ConfigLoader()
        ccq_paths = CCQPaths.from_config(config_loader)
        
        # Discover filings
        print("\nDiscovering filings...")
        discovery = FilingDiscovery(ccq_paths)
        filings = discovery.discover_filings()
        
        if not filings:
            print("\nNo filings found in BOTH Map Pro and CCQ outputs.")
            print("Please ensure both mappers have processed the same filings.")
            return 1
        
        # Interactive loop
        while True:
            display_menu(filings)
            selected_filing = get_user_selection(filings)
            
            if selected_filing is None:
                print("\nExiting Fact Authority. Goodbye!")
                return 0
            
            # Run validation
            success = run_validation(selected_filing, ccq_paths)
            
            # Ask if user wants to continue
            continue_input = input("\nValidate another filing? (y/n): ").strip().lower()
            if continue_input != 'y':
                print("\nExiting Fact Authority. Goodbye!")
                return 0
                
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        return 1
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())