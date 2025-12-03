#!/usr/bin/env python3
"""
Test Taxonomy Loading
=====================

Quick test to verify taxonomy loading fix works.

Run from ccq_val root directory:
    python3 tests/test_taxonomy_loading_fix.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from core.config_loader import ConfigLoader
from core.data_paths import initialize_paths
from engines.fact_authority.taxonomy_interface import TaxonomyAuthorityReader


def test_taxonomy_import():
    """Test that TaxonomyLoader can be imported."""
    print("=" * 70)
    print("TEST 1: Import TaxonomyLoader")
    print("=" * 70)
    
    try:
        from engines.ccq_mapper.loaders.taxonomy_loader import TaxonomyLoader
        print("✓ SUCCESS: TaxonomyLoader imported successfully")
        print(f"  Location: {TaxonomyLoader.__module__}")
        return True
    except ImportError as e:
        print(f"✗ FAILED: Could not import TaxonomyLoader: {e}")
        return False


def test_taxonomy_authority_reader():
    """Test that TaxonomyAuthorityReader initializes."""
    print("\n" + "=" * 70)
    print("TEST 2: Initialize TaxonomyAuthorityReader")
    print("=" * 70)
    
    try:
        reader = TaxonomyAuthorityReader()
        print("✓ SUCCESS: TaxonomyAuthorityReader initialized")
        print(f"  Map Pro path: {reader.map_pro_path}")
        print(f"  Map Pro path exists: {reader.map_pro_path.exists()}")
        return True
    except Exception as e:
        print(f"✗ FAILED: Could not initialize TaxonomyAuthorityReader: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_taxonomy_loading():
    """Test loading taxonomy from actual files."""
    print("\n" + "=" * 70)
    print("TEST 3: Load Taxonomy from Files")
    print("=" * 70)
    
    try:
        # Initialize config and paths
        config = ConfigLoader()
        paths = initialize_paths(config._config)
        
        print(f"Taxonomy base: {paths.taxonomies}")
        print(f"Exists: {paths.taxonomies.exists()}")
        
        # Check for libraries directory
        libraries_dir = paths.taxonomies / 'libraries'
        print(f"\nLibraries directory: {libraries_dir}")
        print(f"Exists: {libraries_dir.exists()}")
        
        if libraries_dir.exists():
            taxonomies = list(libraries_dir.iterdir())
            print(f"Found {len(taxonomies)} taxonomy directories:")
            for tax in taxonomies[:5]:  # Show first 5
                print(f"  - {tax.name}")
        
        # Try to load a taxonomy
        taxonomy_paths = paths.get_taxonomy_paths_for_filing(
            market='sec',
            taxonomy_name='us-gaap',
            taxonomy_version='2024'
        )
        
        if not taxonomy_paths:
            # Try without version
            taxonomy_paths = paths.get_taxonomy_paths_for_filing(
                market='sec',
                taxonomy_name=None,
                taxonomy_version=None
            )
        
        print(f"\nFound {len(taxonomy_paths)} taxonomy paths:")
        for path in taxonomy_paths[:3]:  # Show first 3
            print(f"  - {path}")
            print(f"    Exists: {path.exists()}")
            if path.exists():
                xsd_files = list(path.glob('*.xsd'))
                pre_files = list(path.glob('*_pre.xml'))
                print(f"    XSD files: {len(xsd_files)}")
                print(f"    Presentation linkbases: {len(pre_files)}")
        
        if not taxonomy_paths:
            print("✗ FAILED: No taxonomy paths found")
            return False
        
        # Initialize reader and try to load
        reader = TaxonomyAuthorityReader()
        
        print(f"\nAttempting to load taxonomies...")
        hierarchy = reader.load_filing_taxonomy(taxonomy_paths[:1])  # Load first one
        
        concepts_count = len(hierarchy.get('concepts', {}))
        labels_count = len(hierarchy.get('labels', {}))
        
        print(f"\nResults:")
        print(f"  Concepts loaded: {concepts_count}")
        print(f"  Labels loaded: {labels_count}")
        
        if concepts_count > 0:
            print("✓ SUCCESS: Taxonomy loaded successfully!")
            
            # Show some example concepts
            concepts = hierarchy.get('concepts', {})
            print(f"\nExample concepts (first 5):")
            for i, (qname, data) in enumerate(list(concepts.items())[:5]):
                balance = data.get('balance_type', 'N/A')
                period = data.get('period_type', 'N/A')
                print(f"  {i+1}. {qname}")
                print(f"     Balance: {balance}, Period: {period}")
            
            return True
        else:
            print("✗ FAILED: No concepts loaded")
            print(f"  Metadata: {hierarchy.get('metadata', {})}")
            return False
            
    except Exception as e:
        print(f"✗ FAILED: Error during taxonomy loading: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("TAXONOMY LOADING FIX - VERIFICATION TESTS")
    print("=" * 70)
    
    results = []
    
    # Test 1: Import
    results.append(("Import TaxonomyLoader", test_taxonomy_import()))
    
    # Test 2: Initialize reader
    results.append(("Initialize Reader", test_taxonomy_authority_reader()))
    
    # Test 3: Load taxonomy
    results.append(("Load Taxonomy", test_taxonomy_loading()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Fix is working correctly!")
    else:
        print("✗ SOME TESTS FAILED - Review errors above")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())