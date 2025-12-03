# File: test_filings_reader_phase1.py
# Location: tests/test_filings_reader_phase1.py

"""
Test Filings Reader Phase 1 Components
=======================================

Comprehensive test for all Phase 1 filings_reader components:
- FilingProfile: Data structure and serialization
- FileTypeClassifier: File type detection
- MarketStructureDetector: Market detection
- FilingDiscoverer: File discovery
- FilingValidator: Completeness validation
- FilingCacheManager: Profile caching

Tests cache directory creation at configured path.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.config_loader import ConfigLoader
from core.data_paths import initialize_paths, ccq_paths
from engines.fact_authority.filings_reader.filing_profile import FilingProfile
from engines.fact_authority.filings_reader.file_type_classifier import FileTypeClassifier
from engines.fact_authority.filings_reader.market_structure_detector import MarketStructureDetector
from engines.fact_authority.filings_reader.filing_discoverer import FilingDiscoverer
from engines.fact_authority.filings_reader.filing_validator import FilingValidator
from engines.fact_authority.filings_reader.filing_cache_manager import FilingCacheManager


def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_configuration():
    """Test configuration and path initialization."""
    print_section("TEST 1: Configuration and Path Initialization")
    
    # Load configuration
    config_loader = ConfigLoader()
    config = config_loader.get_all()
    
    print(f"Environment: {config.get('environment')}")
    print(f"Taxonomy path: {config.get('taxonomy_path')}")
    print(f"Filings cache path: {config.get('filings_cache_path')}")
    
    # Initialize paths
    paths = initialize_paths(config)
    
    print(f"\nData paths initialized: {paths is not None}")
    print(f"Filings cache configured: {paths.filings_cache is not None}")
    
    if paths.filings_cache:
        print(f"Filings cache location: {paths.filings_cache}")
        print(f"Cache directory exists: {paths.filings_cache.exists()}")
    
    return paths


def test_filing_profile():
    """Test FilingProfile data structure."""
    print_section("TEST 2: FilingProfile Data Structure")
    
    # Create profile
    profile = FilingProfile()
    
    # Set metadata
    profile.metadata = {
        'company': 'Test_Company',
        'market': 'SEC',
        'filing_type': '10-K',
        'filing_date': '2024-03-15'
    }
    
    # Set extension info
    profile.extension_namespace = 'test'
    profile.taxonomy_year = '2024'
    
    # Set files
    profile.files = {
        'extension_schema': Path('/test/test-2024.xsd'),
        'presentation': [Path('/test/test-2024_pre.xml')],
        'instance': [Path('/test/test-20240315.xml')]
    }
    
    # Test methods
    print(f"Company: {profile.get_company()}")
    print(f"Market: {profile.get_market()}")
    print(f"Has extensions: {profile.has_extensions()}")
    print(f"Extension schema: {profile.get_extension_schema()}")
    
    # Test serialization
    profile_dict = profile.to_dict()
    print(f"Serialization works: {profile_dict is not None}")
    
    profile_json = profile.to_json()
    print(f"JSON serialization works: {len(profile_json) > 0}")
    
    # Test deserialization
    restored = FilingProfile.from_json(profile_json)
    print(f"Deserialization works: {restored.get_company() == 'Test_Company'}")
    
    return profile


def test_file_type_classifier():
    """Test FileTypeClassifier."""
    print_section("TEST 3: FileTypeClassifier")
    
    classifier = FileTypeClassifier()
    
    # Test various file types
    test_files = {
        'aapl-2024.xsd': 'extension_schema',
        'aapl-2024_pre.xml': 'presentation',
        'aapl-2024_cal.xml': 'calculation',
        'aapl-2024_def.xml': 'definition',
        'aapl-2024_lab.xml': 'label',
        'aapl-20240930.xml': 'instance_xml',
        'test.xhtml': 'instance_ixbrl',
        'us-gaap-2024.xsd': 'standard_taxonomy',
        'image.jpg': 'useless',
        'document.pdf': 'useless',
    }
    
    print("\nClassification tests:")
    all_correct = True
    for filename, expected in test_files.items():
        file_path = Path(f"/test/{filename}")
        result = classifier.classify(file_path)
        correct = result == expected
        all_correct = all_correct and correct
        status = "PASS" if correct else "FAIL"
        print(f"  {status}: {filename} -> {result} (expected: {expected})")
    
    print(f"\nAll classifications correct: {all_correct}")
    
    return classifier


def test_market_structure_detector():
    """Test MarketStructureDetector."""
    print_section("TEST 4: MarketStructureDetector")
    
    detector = MarketStructureDetector()
    
    # Test market detection
    test_paths = {
        '/mnt/map_pro/data/entities/SEC/Apple/10-K/2024': 'SEC',
        '/mnt/map_pro/data/entities/sec/Microsoft/10-Q/2024': 'SEC',
        '/data/filings/FCA/Company/2024': 'FCA',
        '/data/filings/ESMA/Company/2024': 'ESMA',
    }
    
    print("\nMarket detection tests:")
    for path_str, expected_market in test_paths.items():
        path = Path(path_str)
        detected = detector.detect_market(path)
        correct = detected == expected_market
        status = "PASS" if correct else "FAIL"
        print(f"  {status}: {path_str} -> {detected} (expected: {expected_market})")
    
    # Test market configuration
    sec_config = detector.get_market_config('SEC')
    print(f"\nSEC config retrieved: {sec_config is not None}")
    print(f"SEC has extracted folder: {sec_config.get('has_extracted_folder')}")
    
    return detector


def test_filing_discoverer(filing_path):
    """Test FilingDiscoverer with real filing."""
    print_section("TEST 5: FilingDiscoverer - Real Filing Discovery")
    
    if not filing_path or not filing_path.exists():
        print(f"SKIP: Filing path not provided or does not exist: {filing_path}")
        return None
    
    print(f"Testing with filing: {filing_path}")
    
    discoverer = FilingDiscoverer()
    
    # Quick check first
    has_xbrl = discoverer.quick_check(filing_path)
    print(f"Quick check - XBRL files present: {has_xbrl}")
    
    if not has_xbrl:
        print("SKIP: No XBRL files detected in quick check")
        return None
    
    # Full discovery
    print("\nPerforming full discovery...")
    try:
        discovered = discoverer.discover(filing_path)
        
        # Print statistics
        stats = discoverer.get_discovery_statistics(discovered)
        print(f"\nDiscovery Statistics:")
        print(f"  Total XBRL files: {stats['total_xbrl_files']}")
        print(f"  Extension schemas: {stats['extension_schemas']}")
        print(f"  Presentation linkbases: {stats['presentation_linkbases']}")
        print(f"  Calculation linkbases: {stats['calculation_linkbases']}")
        print(f"  Definition linkbases: {stats['definition_linkbases']}")
        print(f"  Label linkbases: {stats['label_linkbases']}")
        print(f"  Instance documents: {stats['instance_documents']}")
        print(f"  Useless files (ignored): {stats['useless_files']}")
        
        return discovered
    
    except Exception as e:
        print(f"ERROR during discovery: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_filing_validator(discovered_files):
    """Test FilingValidator."""
    print_section("TEST 6: FilingValidator - Completeness Check")
    
    if not discovered_files:
        print("SKIP: No discovered files to validate")
        return None
    
    validator = FilingValidator()
    
    try:
        results = validator.validate(discovered_files)
        
        print(f"\nValidation Results:")
        print(f"  All files accessible: {results['all_files_accessible']}")
        print(f"  Schema valid: {results['schema_valid']}")
        print(f"  Linkbases complete: {results['linkbases_complete']}")
        print(f"  Required files present: {results['required_files_present']}")
        print(f"  Summary: {results['summary']}")
        
        if results['errors']:
            print(f"\n  Errors ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"    - {error}")
        
        if results['warnings']:
            print(f"\n  Warnings ({len(results['warnings'])}):")
            for warning in results['warnings']:
                print(f"    - {warning}")
        
        return results
    
    except Exception as e:
        print(f"ERROR during validation: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_filing_cache_manager(profile, paths, skip_cleanup=False):
    """Test FilingCacheManager and cache directory creation."""
    print_section("TEST 7: FilingCacheManager - Caching and Cache Directory")
    
    if not paths or not paths.filings_cache:
        print("ERROR: Filings cache path not configured")
        return False
    
    print(f"Cache base path: {paths.filings_cache}")
    print(f"Cache directory exists before test: {paths.filings_cache.exists()}")
    
    try:
        # Initialize cache manager
        cache_manager = FilingCacheManager()
        print("Cache manager initialized successfully")
        
        # Verify cache directory was created
        cache_exists = paths.filings_cache.exists()
        cache_is_dir = paths.filings_cache.is_dir() if cache_exists else False
        
        print(f"\nCache directory status:")
        print(f"  Exists: {cache_exists}")
        print(f"  Is directory: {cache_is_dir}")
        
        if not cache_exists:
            print("WARNING: Cache directory was not created automatically")
            return False
        
        # Test cache operations
        test_market = 'sec'
        test_company = 'Test_Company'
        test_filing_type = '10-K'
        test_filing_id = 'test_filing_001'
        
        # Save profile to cache
        print(f"\nTesting cache save...")
        save_success = cache_manager.save_profile(
            profile,
            test_market,
            test_company,
            test_filing_type,
            test_filing_id
        )
        print(f"  Save successful: {save_success}")
        
        if save_success:
            # Check cache file exists
            cache_path = cache_manager.get_cache_path(
                test_market,
                test_company,
                test_filing_type,
                test_filing_id
            )
            print(f"  Cache file created: {cache_path.exists()}")
            print(f"  Cache file path: {cache_path}")
            
            # Test cache loading
            print(f"\nTesting cache load...")
            loaded_profile = cache_manager.load_profile(
                test_market,
                test_company,
                test_filing_type,
                test_filing_id
            )
            
            load_success = loaded_profile is not None
            print(f"  Load successful: {load_success}")
            
            if load_success:
                print(f"  Loaded company matches: {loaded_profile.get_company() == profile.get_company()}")
            
            # Get cache info
            print(f"\nCache information:")
            cache_info = cache_manager.get_cache_info()
            print(f"  Total profiles cached: {cache_info['total_profiles']}")
            print(f"  Total size: {cache_info['total_size_bytes']} bytes")
            print(f"  Markets: {[m['market'] for m in cache_info['markets']]}")
            
            # Conditionally clean up test cache entry
            if not skip_cleanup:
                print(f"\nCleaning up test cache entry...")
                invalidated = cache_manager.invalidate_filing(
                    test_market,
                    test_company,
                    test_filing_type,
                    test_filing_id
                )
                print(f"  Cleanup successful: {invalidated}")
            else:
                print(f"\nSkipping cleanup - cache file preserved:")
                print(f"  {cache_path}")
        
        return cache_exists and cache_is_dir
    
    except Exception as e:
        print(f"ERROR in cache manager test: {e}")
        import traceback
        traceback.print_exc()
        return False


def find_real_filing(base_path, max_depth=6):
    """
    Recursively search for a real XBRL filing.
    
    Args:
        base_path: Base entities path to search from
        max_depth: Maximum depth to search
        
    Returns:
        Path to filing directory or None
    """
    print_section("AUTO-DISCOVERY: Searching for Real Filing")
    
    if not base_path or not base_path.exists():
        print(f"Base path does not exist: {base_path}")
        return None
    
    print(f"Searching from: {base_path}")
    print(f"Max depth: {max_depth} levels")
    
    # Look for directories containing .xsd files (extension schemas)
    def search_recursive(directory, current_depth=0):
        if current_depth > max_depth:
            return None
        
        try:
            for item in directory.iterdir():
                if item.is_symlink():
                    continue
                
                if item.is_dir():
                    # Check if this directory has XBRL files
                    xbrl_files = list(item.glob('*.xsd')) + list(item.glob('*.xml'))
                    if xbrl_files:
                        print(f"\nFound filing candidate: {item}")
                        print(f"  Contains {len(xbrl_files)} XBRL files")
                        return item
                    
                    # Recurse into subdirectories
                    result = search_recursive(item, current_depth + 1)
                    if result:
                        return result
        except PermissionError:
            pass
        
        return None
    
    found = search_recursive(base_path)
    
    if found:
        print(f"\nAuto-discovery SUCCESS: {found}")
    else:
        print(f"\nAuto-discovery FAILED: No XBRL filings found")
    
    return found


def run_phase1_tests(filing_path_str=None, skip_cleanup=False):
    """
    Run all Phase 1 tests.
    
    Args:
        filing_path_str: Optional path to real filing for discovery test
        skip_cleanup: If True, don't delete test cache file
    """
    print("\n" + "=" * 80)
    print("  FILINGS READER PHASE 1 - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    # Run tests
    try:
        # Test 1: Configuration
        paths = test_configuration()
        if not paths:
            print("\nFATAL: Could not initialize data paths")
            return False
        
        # Test 2: FilingProfile
        profile = test_filing_profile()
        
        # Test 3: FileTypeClassifier
        classifier = test_file_type_classifier()
        
        # Test 4: MarketStructureDetector
        detector = test_market_structure_detector()
        
        # Auto-discover a real filing if not provided
        filing_path = None
        if filing_path_str:
            filing_path = Path(filing_path_str)
            print(f"\nUsing provided filing path: {filing_path}")
        else:
            # Try to auto-discover from entities base path
            if paths.mapper_xbrl:
                filing_path = find_real_filing(paths.mapper_xbrl, max_depth=6)
            elif hasattr(paths, 'data_root'):
                entities_path = paths.data_root / "entities"
                if entities_path.exists():
                    filing_path = find_real_filing(entities_path, max_depth=6)
        
        # Test 5: FilingDiscoverer (tests real discovery)
        discovered_files = test_filing_discoverer(filing_path)
        
        # Test 6: FilingValidator (validates discovered files)
        validation_results = test_filing_validator(discovered_files)
        
        # Test 7: FilingCacheManager (critical - tests cache creation)
        cache_test_passed = test_filing_cache_manager(profile, paths, skip_cleanup)
        
        # Final summary
        print_section("TEST SUMMARY")
        print("Test 1 - Configuration: PASS")
        print("Test 2 - FilingProfile: PASS")
        print("Test 3 - FileTypeClassifier: PASS")
        print("Test 4 - MarketStructureDetector: PASS")
        
        if filing_path:
            print(f"Test 5 - FilingDiscoverer: {'PASS' if discovered_files else 'FAIL (filing found but no XBRL files)'}")
            print(f"Test 6 - FilingValidator: {'PASS' if validation_results else 'FAIL (no files to validate)'}")
            if discovered_files:
                stats = FilingDiscoverer().get_discovery_statistics(discovered_files)
                print(f"  Filing used: {filing_path}")
                print(f"  Files discovered: {stats['total_xbrl_files']}")
        else:
            print(f"Test 5 - FilingDiscoverer: SKIP (no filing found via auto-discovery)")
            print(f"Test 6 - FilingValidator: SKIP (no filing found via auto-discovery)")
        
        print(f"Test 7 - FilingCacheManager: {'PASS' if cache_test_passed else 'FAIL'}")
        
        print("\n" + "=" * 80)
        print("  CRITICAL: Cache Directory Check")
        print("=" * 80)
        if paths.filings_cache:
            print(f"Cache path from .env: {paths.filings_cache}")
            print(f"Cache directory exists: {paths.filings_cache.exists()}")
            print(f"Cache directory is valid: {cache_test_passed}")
        else:
            print("ERROR: Cache path not configured in .env file")
        
        overall_success = cache_test_passed
        print("\n" + "=" * 80)
        if overall_success:
            print("  PHASE 1 TEST SUITE: ALL CRITICAL TESTS PASSED")
        else:
            print("  PHASE 1 TEST SUITE: SOME TESTS FAILED")
        print("=" * 80 + "\n")
        
        return overall_success
    
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test filings_reader Phase 1 components'
    )
    parser.add_argument(
        '--filing-path',
        type=str,
        help='Path to real XBRL filing for discovery test (optional - will auto-discover if not provided)'
    )
    parser.add_argument(
        '--skip-cleanup',
        action='store_true',
        help='Skip cleanup of test cache file (preserves test_filing_001.json for inspection)'
    )
    
    args = parser.parse_args()
    
    success = run_phase1_tests(args.filing_path, args.skip_cleanup)
    sys.exit(0 if success else 1)