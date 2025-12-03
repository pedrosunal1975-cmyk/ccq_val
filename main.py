"""
CCQ Validator Entry Point

Main entry point for the Content Consistency and Quality Validator.
Initializes core systems and provides command-line interface.
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core import ConfigLoader, SystemLogger, DatabaseCoordinator
from core.data_paths import initialize_paths, ccq_paths
from core.ccq_coordinator import CCQCoordinator
from shared.exceptions import CCQException, ConfigurationError


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='CCQ Validator - Financial Statement Validation System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a specific filing by ID
  python main.py --filing-id abc123-def456-ghi789
  
  # Process all filings in a directory
  python main.py --scan-all
  
  # Process filings for a specific company
  python main.py --entity "Apple Inc"
  
  # List available filings
  python main.py --list
        """
    )
    
    # Processing modes (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--filing-id',
        type=str,
        help='Process a specific filing by UUID'
    )
    mode_group.add_argument(
        '--scan-all',
        action='store_true',
        help='Scan and process all available filings'
    )
    mode_group.add_argument(
        '--entity',
        type=str,
        help='Process all filings for a specific entity name'
    )
    mode_group.add_argument(
        '--list',
        action='store_true',
        help='List all available filings without processing'
    )
    
    # Optional filters
    parser.add_argument(
        '--market',
        type=str,
        choices=['sec', 'uk', 'eu'],
        help='Filter by market type'
    )
    parser.add_argument(
        '--filing-type',
        type=str,
        help='Filter by filing type (e.g., 10-K, 10-Q)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of filings to process'
    )
    
    # Options
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reprocessing even if already validated'
    )
    parser.add_argument(
        '--skip-db',
        action='store_true',
        help='Skip database recording (useful for testing)'
    )
    
    return parser.parse_args()


def initialize_system() -> tuple:
    """
    Initialize all core systems.
    
    Returns:
        Tuple of (config, logger, path_manager, db_coordinator)
        
    Raises:
        ConfigurationError: If initialization fails
    """
    try:
        # Initialize configuration first
        config = ConfigLoader()
        
        # Initialize logger
        logger = SystemLogger().get_logger(__name__)
        logger.info("="*60)
        logger.info("CCQ Validator System Initializing")
        logger.info("="*60)
        
        # Log configuration
        logger.info(f"Environment: {config.get('environment')}")
        logger.info(f"Debug Mode: {config.get('debug')}")
        logger.info(f"Log Level: {config.get('log_level')}")
        
        # Initialize path manager with config
        path_manager = initialize_paths({
            'CCQ_DATA_ROOT': str(config.get('data_root')),
            'CCQ_INPUT_PATH': str(config.get('input_path')),
            'CCQ_OUTPUT_PATH': str(config.get('output_path')),
            'CCQ_TAXONOMY_PATH': str(config.get('taxonomy_path')),
            'CCQ_PARSED_FACTS_PATH': str(config.get('parsed_facts_path'))
        })
        logger.info(f"Data Root: {path_manager.data_root}")
        logger.info(f"Input Path: {path_manager.input_mapped}")
        logger.info(f"Output Path: {path_manager.output_validated}")
        logger.info(f"Taxonomy Path: {path_manager.taxonomies}")
        logger.info(f"Parsed Facts Path: {path_manager.parsed_facts}")
        
        # Initialize database coordinator
        db_coordinator = DatabaseCoordinator()
        
        # Test database connection
        if db_coordinator.test_connection():
            logger.info("Database connection: OK")
        else:
            logger.warning("Database connection: FAILED")
        
        logger.info("="*60)
        logger.info("CCQ Validator System Initialized Successfully")
        logger.info("="*60)
        
        return config, logger, path_manager, db_coordinator
        
    except Exception as e:
        print(f"FATAL: System initialization failed: {str(e)}", file=sys.stderr)
        raise ConfigurationError(f"System initialization failed: {str(e)}") from e


def list_available_filings(logger, path_manager) -> None:
    """
    List all available filings in the input directory.
    
    Args:
        logger: Logger instance
        path_manager: Path manager instance
    """
    logger.info("Scanning for available filings...")
    
    input_dir = path_manager.input_mapped
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return
    
    # Scan for JSON files (Map Pro output)
    filing_count = 0
    
    for market_dir in sorted(input_dir.iterdir()):
        if not market_dir.is_dir():
            continue
        
        market_name = market_dir.name
        logger.info(f"\nMarket: {market_name}")
        logger.info("-" * 60)
        
        for json_file in sorted(market_dir.rglob('*.json')):
            # Skip CCQ output files
            if 'ccq_' in json_file.name or 'normalized' in json_file.name:
                continue
            
            # Get relative path for display
            rel_path = json_file.relative_to(input_dir)
            logger.info(f"  {rel_path}")
            filing_count += 1
    
    logger.info(f"\nTotal filings found: {filing_count}")

async def process_filing_by_path(
    filing_path: Path,
    coordinator: CCQCoordinator,
    logger,
    force: bool = False
) -> bool:
    """
    Process a filing by its directory path.
    
    Args:
        filing_path: Path to filing directory
        coordinator: CCQ coordinator instance
        logger: Logger instance
        force: Force reprocessing if already validated
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing filing at: {filing_path}")
    
    try:
        # Extract metadata from path
        # Path format: .../market/entity/filing_type/date/
        parts = filing_path.parts
        market = parts[-4]
        entity = parts[-3]
        filing_type = parts[-2]
        filing_date = parts[-1]
        
        # Create a pseudo filing_id from path
        filing_id = f"{market}_{entity}_{filing_type}_{filing_date}"
        
        logger.info(f"Processing: {entity} - {filing_type} - {filing_date}")
        
        # Process through CCQ pipeline
        # Pass the path so coordinator can load files directly
        result = await coordinator.validate_filing_from_path(
            filing_path=filing_path,
            filing_id=filing_id,
            force=force
        )
        
        if result['success']:
            logger.info(f"✅ Filing validated successfully")
            logger.info(f"   Confidence Score: {result['confidence_score']:.2f}/100")
            logger.info(f"   Category: {result['category']}")
            logger.info(f"   Ready for Analysis: {result['ready_for_analysis']}")
            logger.info(f"   Report: {result.get('report_path', 'N/A')}")
            return True
        else:
            logger.error(f"❌ Validation failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing filing at {filing_path}: {e}", exc_info=True)
        return False

async def scan_and_process_all(
    coordinator: CCQCoordinator,
    logger,
    path_manager,
    market: Optional[str] = None,
    filing_type: Optional[str] = None,
    limit: Optional[int] = None,
    force: bool = False
) -> dict:
    """
    Scan input directory and process all filings.
    
    Args:
        coordinator: CCQ coordinator instance
        logger: Logger instance
        path_manager: Path manager instance
        market: Optional market filter
        filing_type: Optional filing type filter
        limit: Optional limit on number to process
        force: Force reprocessing
        
    Returns:
        Dictionary with processing statistics
    """
    logger.info("Scanning for filings to process...")
    
    stats = {
        'total_found': 0,
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'skipped': 0
    }
    
    input_dir = path_manager.input_mapped
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return stats
    
    # Collect all filing directories
    filings_to_process = []
    
    for market_dir in sorted(input_dir.iterdir()):
        if not market_dir.is_dir():
            continue
        
        # Apply market filter
        if market and market_dir.name != market:
            continue
        
        # Scan for entity directories
        for entity_dir in sorted(market_dir.iterdir()):
            if not entity_dir.is_dir():
                continue
            
            # Scan for filing type directories
            for type_dir in sorted(entity_dir.iterdir()):
                if not type_dir.is_dir():
                    continue
                
                # Apply filing type filter
                if filing_type and type_dir.name != filing_type:
                    continue
                
                # Scan for date directories
                for date_dir in sorted(type_dir.iterdir()):
                    if not date_dir.is_dir():
                        continue
                    
                    # Check if this directory has statement files
                    statement_files = list(date_dir.glob('*.json'))
                    if not statement_files:
                        continue
                    
                    # Exclude CCQ output files
                    statement_files = [
                        f for f in statement_files 
                        if 'ccq_' not in f.name and 'normalized' not in f.name
                    ]
                    
                    if not statement_files:
                        continue
                    
                    filing_info = {
                        'path': date_dir,
                        'market': market_dir.name,
                        'entity': entity_dir.name,
                        'filing_type': type_dir.name,
                        'date': date_dir.name,
                        'file_count': len(statement_files)
                    }
                    
                    filings_to_process.append(filing_info)
                    stats['total_found'] += 1
                    
                    # Apply limit
                    if limit and len(filings_to_process) >= limit:
                        break
                
                if limit and len(filings_to_process) >= limit:
                    break
            
            if limit and len(filings_to_process) >= limit:
                break
        
        if limit and len(filings_to_process) >= limit:
            break
    
    logger.info(f"Found {stats['total_found']} filings to process")
    
    # Process each filing
    for i, filing_info in enumerate(filings_to_process, 1):
        logger.info(
            f"\n[{i}/{len(filings_to_process)}] "
            f"{filing_info['entity']} - {filing_info['filing_type']} - {filing_info['date']} "
            f"({filing_info['file_count']} files)"
        )
        
        try:
            success = await process_filing_by_path(
                filing_info['path'],
                coordinator,
                logger,
                force
            )
            
            stats['processed'] += 1
            if success:
                stats['successful'] += 1
            else:
                stats['failed'] += 1
                
        except Exception as e:
            logger.error(f"Error processing filing: {e}")
            stats['failed'] += 1
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("PROCESSING SUMMARY")
    logger.info("="*60)
    logger.info(f"Total Found:    {stats['total_found']}")
    logger.info(f"Processed:      {stats['processed']}")
    logger.info(f"Successful:     {stats['successful']}")
    logger.info(f"Failed:         {stats['failed']}")
    logger.info(f"Skipped:        {stats['skipped']}")
    logger.info("="*60)
    
    return stats


def shutdown_system(db_coordinator: DatabaseCoordinator, logger) -> None:
    """
    Gracefully shutdown all systems.
    
    Args:
        db_coordinator: Database coordinator to close
        logger: Logger instance
    """
    logger.info("Shutting down CCQ Validator...")
    
    try:
        db_coordinator.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
    
    logger.info("CCQ Validator shutdown complete")


async def async_main(args: argparse.Namespace) -> int:
    """
    Async main function for processing.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    try:
        # Initialize system
        config, logger, path_manager, db_coordinator = initialize_system()
        
        # Initialize CCQ coordinator
        coordinator = CCQCoordinator(
            config=config.get_all(),
            db_coordinator=db_coordinator if not args.skip_db else None
        )
        
        logger.info("CCQ Validator ready for processing")
        
        # Execute based on command-line arguments
        if args.list:
            # Just list available filings
            list_available_filings(logger, path_manager)
            
        elif args.scan_all:
            # Process all filings
            stats = await scan_and_process_all(
                coordinator,
                logger,
                path_manager,
                market=args.market,
                filing_type=args.filing_type,
                limit=args.limit,
                force=args.force
            )
            if stats['failed'] > 0 and stats['successful'] == 0:
                return 1
            
        else:
            # No action specified - show help
            logger.error("No action specified. Use --help for usage information.")
            logger.info("Try: python main.py --scan-all --limit 1")
            return 1
        
        # Clean shutdown
        shutdown_system(db_coordinator, logger)
        
        return 0
        
    except CCQException as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"UNEXPECTED ERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main() -> int:
    """
    Main entry point for CCQ Validator.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse arguments
    args = parse_arguments()
    
    # Run async main
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    sys.exit(main())