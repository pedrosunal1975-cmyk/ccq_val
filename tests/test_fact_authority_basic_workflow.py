# File: tests/test_fact_authority_basic_workflow.py
# Test: Basic workflow through fact_authority orchestrator
# Run from project root: python tests/test_fact_authority_basic_workflow.py

"""
Test Basic Fact Authority Workflow
===================================

Tests the basic workflow through fact_authority.py orchestrator:
1. Initialization
2. Load phase (statements, facts, taxonomies, XBRL)
3. Process phase (reconciliation, null quality)
4. Output phase (without writing files)

This test verifies that the orchestrator coordinates all components
correctly, even with placeholder taxonomy integration.

Expected behavior with taxonomy placeholders:
- Load phase: Should complete successfully
- Process phase: Should complete with warnings about empty taxonomy
- Statistics: Will show 0 matches (expected until taxonomy integration)
"""

import sys
from pathlib import Path
from pprint import pprint

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from core.config_loader import ConfigLoader
from core.data_paths import CCQPaths
from engines.fact_authority import FactAuthority


# Test data - PLUG_POWER_INC
TEST_FILING = {
    'market': 'sec',
    'entity_name': 'PLUG_POWER_INC',
    'filing_type': '10-K',
    'filing_date': '2025-03-03'
}


def test_initialization():
    """Test fact authority initialization."""
    print("=" * 80)
    print("TEST 1: Initialization")
    print("=" * 80)
    
    try:
        config = ConfigLoader()
        ccq_paths = CCQPaths.from_config(config)
        fact_authority = FactAuthority(ccq_paths)
        
        print("✓ FactAuthority initialized successfully")
        print(f"  CCQPaths: {ccq_paths is not None}")
        print(f"  Input path: {ccq_paths.input_mapped}")
        print(f"  Mapper output: {ccq_paths.mapper_output}")
        print(f"  Unified output: {ccq_paths.unified_mapped}")
        
        return True, fact_authority
        
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_load_phase(fact_authority):
    """Test the load phase of validation."""
    print("\n" + "=" * 80)
    print("TEST 2: Load Phase")
    print("=" * 80)
    
    print(f"\nAttempting to load filing:")
    print(f"  Market: {TEST_FILING['market']}")
    print(f"  Entity: {TEST_FILING['entity_name']}")
    print(f"  Type: {TEST_FILING['filing_type']}")
    print(f"  Date: {TEST_FILING['filing_date']}")
    print()
    
    try:
        # Call the private _load_phase method directly
        load_result = fact_authority._load_phase(
            TEST_FILING['market'],
            TEST_FILING['entity_name'],
            TEST_FILING['filing_type'],
            TEST_FILING['filing_date']
        )
        
        if not load_result['success']:
            print("✗ Load phase failed")
            print(f"  Errors: {load_result.get('errors', [])}")
            return False, None
        
        print("✓ Load phase completed successfully")
        
        data = load_result['data']
        
        # Check what was loaded
        print("\nData loaded:")
        print(f"  - Map Pro statements: {'map_pro_statements' in data}")
        print(f"  - CCQ statements: {'ccq_statements' in data}")
        print(f"  - Facts data: {'facts_data' in data}")
        print(f"  - Namespaces: {data.get('namespaces', set())}")
        print(f"  - Taxonomy data: {'taxonomy_data' in data}")
        print(f"  - Filing data: {'filing_data' in data}")
        
        # Check statement counts
        if 'map_pro_statements' in data:
            mp_meta = data['map_pro_statements'].get('metadata', {})
            print(f"\n  Map Pro: {mp_meta.get('total_facts', 0)} total facts")
        
        if 'ccq_statements' in data:
            ccq_meta = data['ccq_statements'].get('metadata', {})
            print(f"  CCQ: {ccq_meta.get('total_facts', 0)} total facts")
        
        return True, data
        
    except FileNotFoundError as e:
        print(f"⚠ File not found: {e}")
        print("\nCheck data paths:")
        print(f"  Map Pro: /mnt/map_pro/data/mapped_statements/sec/PLUG_POWER_INC/10-K/2025-03-03/")
        print(f"  CCQ: /mnt/map_pro/data/ccq_mapped/sec/PLUG_POWER_INC/10-K/2025-03-03/")
        return False, None
        
    except Exception as e:
        print(f"✗ Load phase error: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_process_phase(fact_authority, load_data):
    """Test the process phase of validation."""
    print("\n" + "=" * 80)
    print("TEST 3: Process Phase")
    print("=" * 80)
    
    print("\nNote: Taxonomy integration is placeholder, expect warnings")
    print()
    
    try:
        # Call the private _process_phase method directly
        process_result = fact_authority._process_phase(load_data)
        
        if not process_result['success']:
            print("✗ Process phase failed")
            print(f"  Errors: {process_result.get('errors', [])}")
            return False, None
        
        print("✓ Process phase completed successfully")
        
        data = process_result['data']
        
        # Check what was processed
        print("\nData processed:")
        print(f"  - Reconciliation result: {'reconciliation' in data}")
        print(f"  - Null analysis: {'null_analysis' in data}")
        print(f"  - Report: {'report' in data}")
        print(f"  - Statistics: {'statistics' in data}")
        
        # Show reconciliation statistics
        if 'reconciliation' in data:
            overall_stats = data['reconciliation'].get('overall_statistics', {})
            print(f"\nReconciliation statistics:")
            print(f"  - Total concepts: {overall_stats.get('total_concepts', 0)}")
            print(f"  - Taxonomy correct both: {overall_stats.get('taxonomy_correct_both', 0)}")
            print(f"  - Map Pro facts: {overall_stats.get('map_pro_facts', 0)}")
            print(f"  - CCQ facts: {overall_stats.get('ccq_facts', 0)}")
            print(f"  - Not in taxonomy: {overall_stats.get('not_in_taxonomy', 0)}")
            
            print("\n⚠ Note: Low matches expected with placeholder taxonomy integration")
        
        # Show null analysis
        if 'null_analysis' in data:
            null_stats = data['null_analysis']
            print(f"\nNull quality analysis:")
            print(f"  - Map Pro nulls: {null_stats.get('map_pro_null_count', 0)}")
            print(f"  - CCQ nulls: {null_stats.get('ccq_null_count', 0)}")
            print(f"  - Common nulls: {len(null_stats.get('common_null_concepts', []))}")
        
        return True, data
        
    except Exception as e:
        print(f"✗ Process phase error: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_full_workflow_no_output(fact_authority):
    """Test full workflow without writing output."""
    print("\n" + "=" * 80)
    print("TEST 4: Full Workflow (No Output)")
    print("=" * 80)
    
    print("\nRunning complete validation workflow...")
    print("(write_output=False to skip file writing)")
    print()
    
    try:
        result = fact_authority.validate_filing(
            market=TEST_FILING['market'],
            entity_name=TEST_FILING['entity_name'],
            filing_type=TEST_FILING['filing_type'],
            filing_date=TEST_FILING['filing_date'],
            write_output=False  # Don't write files
        )
        
        if not result['success']:
            print("✗ Validation failed")
            print(f"  Phase: {result.get('phase', 'unknown')}")
            print(f"  Errors: {result.get('errors', [])}")
            return False
        
        print("✓ Validation completed successfully")
        
        # Show results
        print("\nValidation results:")
        print(f"  - Success: {result['success']}")
        
        if 'statistics' in result:
            stats = result['statistics']
            print(f"\n  Statistics:")
            for key, value in stats.items():
                print(f"    - {key}: {value}")
        
        if 'report' in result:
            report = result['report']
            if 'executive_summary' in report:
                summary = report['executive_summary']
                print(f"\n  Executive summary:")
                print(f"    - Total concepts: {summary.get('total_concepts_validated', 0)}")
                print(f"    - Correctness: {summary.get('correctness_percentage', 0)}%")
                print(f"    - Quality: {summary.get('overall_quality', 'N/A')}")
        
        print("\n⚠ Note: Full functionality requires taxonomy integration")
        print("   See: test_taxonomy_reader_output_structure.py")
        
        return True
        
    except Exception as e:
        print(f"✗ Full workflow error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all workflow tests."""
    print("=" * 80)
    print("FACT AUTHORITY - BASIC WORKFLOW TESTS")
    print("=" * 80)
    print(f"\nTest Filing: PLUG_POWER_INC 10-K (2025-03-03)")
    print()
    
    results = []
    
    # Test 1: Initialization
    success, fact_authority = test_initialization()
    results.append(success)
    
    if not success:
        print("\n✗ Cannot proceed - initialization failed")
        return 1
    
    # Test 2: Load phase
    success, load_data = test_load_phase(fact_authority)
    results.append(success)
    
    if not success:
        print("\n⚠ Cannot proceed - load phase failed")
        print("   Check that PLUG_POWER_INC data exists in both paths")
        return 1
    
    # Test 3: Process phase
    success, process_data = test_process_phase(fact_authority, load_data)
    results.append(success)
    
    # Test 4: Full workflow
    success = test_full_workflow_no_output(fact_authority)
    results.append(success)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    print(f"Test data: PLUG_POWER_INC (10-K/2025-03-03)")
    
    if all(results):
        print("\n✓ ALL WORKFLOW TESTS PASSED")
        print("\nBasic workflow is functional!")
        print("\nNext steps:")
        print("  1. Complete taxonomy integration")
        print("  2. Run: python tests/test_taxonomy_reader_output_structure.py")
        print("  3. Update 4 placeholder methods in:")
        print("     - statement_reconciler._extract_taxonomy_concepts()")
        print("     - statement_classifier._extract_concept_statements()")
        print("     - extension_inheritance_tracer._get_base_concepts()")
        print("     - xbrl_filings._extract_base_concepts()")
        return 0
    else:
        print("\n⚠ SOME TESTS FAILED")
        print("\nCheck:")
        print("  1. PLUG_POWER_INC data availability")
        print("  2. Path configuration (.env)")
        print("  3. Error messages above")
        return 1


if __name__ == '__main__':
    sys.exit(main())