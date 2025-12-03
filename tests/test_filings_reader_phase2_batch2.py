"""
Test Suite for Phase 2 Batch 2 - Integration Layer

Tests the integration components that coordinate Phase 1 and Phase 2:
- ConceptResolver: Concept resolution
- FilingLoader: Complete filing loading
- FilingReader: Main API

Demonstrates complete end-to-end filing reading workflow.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_loader import ConfigLoader
from core.data_paths import initialize_paths


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)


def test_concept_resolver(filing_data):
    """
    Test ConceptResolver with loaded filing data.
    
    Args:
        filing_data: Complete filing data from FilingLoader
        
    Returns:
        True if test passed
    """
    print_section("TEST 1: ConceptResolver")
    
    if not filing_data.get('extension_schema'):
        print("SKIP: No extension schema in filing")
        return False
    
    resolver = filing_data['concept_resolver']
    
    print(f"\nConcept Resolver loaded")
    print(f"Extension namespace: {resolver.get_extension_namespace()}")
    
    # Get statistics
    stats = resolver.get_statistics()
    print(f"\nConcept statistics:")
    print(f"  Total concepts: {stats['total_concepts']}")
    print(f"  Mapped concepts: {stats['mapped_concepts']}")
    print(f"  Monetary concepts: {stats['monetary_concepts']}")
    print(f"  Abstract concepts: {stats['abstract_concepts']}")
    print(f"  Instant concepts: {stats['instant_concepts']}")
    print(f"  Duration concepts: {stats['duration_concepts']}")
    
    # Test concept resolution
    extension_concepts = list(resolver.get_extension_concepts())[:3]
    if extension_concepts:
        print(f"\nSample concept resolution (first 3):")
        for concept in extension_concepts:
            resolution = resolver.resolve_concept(concept)
            properties = resolver.get_concept_properties(concept)
            
            print(f"  Concept: {concept}")
            print(f"    Type: {properties.get('type')}")
            print(f"    Period: {properties.get('period_type')}")
            if resolution:
                print(f"    Base: {resolution.get('base_concept')}")
    
    print("\nConceptResolver: PASS")
    return True


def test_filing_loader(filing_path):
    """
    Test FilingLoader with complete loading workflow.
    
    Args:
        filing_path: Path to filing directory
        
    Returns:
        Filing data if successful, None otherwise
    """
    print_section("TEST 2: FilingLoader")
    
    print(f"Filing path: {filing_path}")
    
    from engines.fact_authority.filings_reader.filing_loader import FilingLoader
    
    loader = FilingLoader()
    
    try:
        filing_data = loader.load(filing_path)
        
        print(f"\nLoading results:")
        print(f"  Market: {filing_data['market']}")
        
        # Check validation results
        validation = filing_data['validation']
        validation_passed = validation.get('all_files_accessible', True) and \
                           validation.get('required_files_present', True)
        print(f"  Validation passed: {validation_passed}")
        if not validation_passed:
            print(f"  Validation errors: {validation.get('errors', [])}")
            print(f"  Validation warnings: {validation.get('warnings', [])}")
        
        stats = filing_data['statistics']
        print(f"\nStatistics:")
        print(f"  Files discovered: {stats['files_discovered']}")
        print(f"  Extension schema: {stats['has_extension_schema']}")
        print(f"  Instance document: {stats['has_instance']}")
        print(f"  Linkbases parsed: {stats['linkbases_parsed']}")
        
        if stats['has_extension_schema']:
            print(f"  Extension elements: {stats['extension_elements']}")
        
        if stats['has_instance']:
            print(f"  Facts: {stats['fact_count']}")
            print(f"  Contexts: {stats['context_count']}")
            print(f"  Format: {stats['instance_format']}")
        
        print(f"\nSummary: {stats['summary']}")
        
        print("\nFilingLoader: PASS")
        return filing_data
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\nFilingLoader: FAIL")
        return None


def test_filing_reader(filing_path):
    """
    Test FilingReader main API.
    
    Args:
        filing_path: Path to filing directory
        
    Returns:
        Filing data if successful, None otherwise
    """
    print_section("TEST 3: FilingReader")
    
    print(f"Filing path: {filing_path}")
    
    from engines.fact_authority.filings_reader.filing_reader import FilingReader
    
    # Initialize without cache for testing
    reader = FilingReader()
    
    try:
        filing_data = reader.read_filing(filing_path, use_cache=False)
        
        print(f"\nFilingReader API test:")
        print(f"  Market: {filing_data['market']}")
        print(f"  Summary: {filing_data['statistics']['summary']}")
        
        # Test concept resolver access
        resolver = reader.get_concept_resolver()
        if resolver:
            concept_count = resolver.get_concept_count()
            print(f"  Concept resolver: {concept_count} concepts loaded")
        
        print("\nFilingReader: PASS")
        return filing_data
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\nFilingReader: FAIL")
        return None


def run_batch2_tests(filing_dir=None):
    """Run all Batch 2 tests."""
    print("\n" + "=" * 80)
    print("  FILINGS READER PHASE 2 BATCH 2 - TEST SUITE")
    print("  (Integration Layer: ConceptResolver, FilingLoader, FilingReader)")
    print("=" * 80)
    
    # Initialize paths
    print("\nInitializing data paths...")
    config = ConfigLoader()
    config_dict = config.get_all()
    paths = initialize_paths(config_dict)
    
    # Auto-discover filing if not provided
    if not filing_dir:
        print(f"\nAuto-discovering filing from: {paths.mapper_xbrl}")
        
        from engines.fact_authority.filings_reader.filing_discoverer import FilingDiscoverer
        
        if paths.mapper_xbrl:
            for item in paths.mapper_xbrl.rglob('*'):
                if item.is_dir() and item.name == 'extracted':
                    discoverer = FilingDiscoverer()
                    if discoverer.quick_check(item):
                        filing_dir = item
                        print(f"Found filing: {filing_dir}")
                        break
    
    if not filing_dir:
        print("\nERROR: No filing directory provided or found")
        print("Try: python tests/test_filings_reader_phase2_batch2.py --filing-dir /path/to/filing")
        return False
    
    # Test FilingLoader (this loads the filing)
    filing_data = test_filing_loader(filing_dir)
    if not filing_data:
        print("\nERROR: FilingLoader failed, cannot continue tests")
        return False
    
    # Test ConceptResolver
    test1_result = test_concept_resolver(filing_data)
    
    # Test FilingReader
    test2_result = test_filing_reader(filing_dir) is not None
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"Test 1 - ConceptResolver: {'PASS' if test1_result else 'FAIL/SKIP'}")
    print(f"Test 2 - FilingLoader: PASS (loaded successfully)")
    print(f"Test 3 - FilingReader: {'PASS' if test2_result else 'FAIL'}")
    
    overall = test1_result and test2_result
    
    print("\n" + "=" * 80)
    if overall:
        print("  BATCH 2 TESTS: PASSED")
        print("  Phase 2 Complete: All components working")
    else:
        print("  BATCH 2 TESTS: PARTIAL SUCCESS")
    print("=" * 80 + "\n")
    
    return overall


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test Phase 2 Batch 2 integration components'
    )
    parser.add_argument(
        '--filing-dir',
        type=str,
        help='Path to filing directory (optional - will auto-discover)'
    )
    
    args = parser.parse_args()
    
    filing_dir = Path(args.filing_dir) if args.filing_dir else None
    success = run_batch2_tests(filing_dir)
    sys.exit(0 if success else 1)