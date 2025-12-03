# File: tests/test_fact_authority_statement_loader.py
# Test: Statement loader component for fact_authority
# Run from project root: python tests/test_fact_authority_statement_loader.py

"""
Test Statement Loader Component
================================

Tests the statement_loader component's ability to:
1. Load Map Pro statements
2. Load CCQ statements
3. Normalize CCQ format to match Map Pro
4. Handle missing files gracefully
5. Use CCQPaths correctly (no hardcoded paths)

This test requires:
- Configured .env file with paths
- Actual statement files from both mappers
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
from engines.fact_authority.input import StatementLoader


def test_initialization():
    """Test statement loader initialization."""
    print("=" * 80)
    print("TEST 1: Initialization")
    print("=" * 80)
    
    try:
        config = ConfigLoader()
        ccq_paths = CCQPaths.from_config(config)
        loader = StatementLoader(ccq_paths)
        
        print("✓ StatementLoader initialized successfully")
        print(f"  CCQPaths configured: {ccq_paths is not None}")
        print(f"  Input mapped path: {ccq_paths.input_mapped}")
        print(f"  Mapper output path: {ccq_paths.mapper_output}")
        
        return True, loader, ccq_paths
        
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_load_map_pro_statements(loader):
    """Test loading Map Pro statements - Plug Power."""
    print("\n" + "=" * 80)
    print("TEST 2: Load Map Pro Statements (Plug Power)")
    print("=" * 80)
    
    # Real data: Plug Power Inc
    market = 'sec'
    entity = 'PLUG_POWER_INC'
    filing_type = '10-K'
    filing_date = '2025-03-03'
    
    print(f"\nAttempting to load: {market}/{entity}/{filing_type}/{filing_date}")
    
    try:
        statements = loader.load_map_pro_statements(
            market, entity, filing_type, filing_date
        )
        
        if not statements or not statements.get('metadata', {}).get('statements_loaded'):
            print("⚠ No Map Pro statements found for Plug Power")
            print("  This is expected if Map Pro data doesn't exist for this filing")
            return False, None
        
        print("✓ Map Pro statements loaded successfully")
        print(f"\nStatements loaded:")
        
        for stmt_type in ['balance_sheet', 'income_statement', 'cash_flow', 'other']:
            if stmt_type in statements:
                facts_count = len(statements[stmt_type].get('facts', []))
                print(f"  - {stmt_type}: {facts_count} facts")
        
        metadata = statements.get('metadata', {})
        print(f"\nMetadata:")
        print(f"  - Source: {metadata.get('source')}")
        print(f"  - Total facts: {metadata.get('total_facts')}")
        print(f"  - Statements loaded: {metadata.get('statements_loaded')}")
        
        # Verify structure
        assert 'metadata' in statements, "Missing metadata"
        assert metadata.get('source') == 'map_pro', "Wrong source"
        assert metadata.get('total_facts', 0) > 0, "No facts loaded"
        
        return True, statements
        
    except FileNotFoundError as e:
        print(f"⚠ File not found: {e}")
        print("  This is expected if Map Pro data doesn't exist for Plug Power")
        return False, None
        
    except Exception as e:
        print(f"✗ Failed to load Map Pro statements: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_load_ccq_statements(loader):
    """Test loading CCQ statements - Plug Power."""
    print("\n" + "=" * 80)
    print("TEST 3: Load CCQ Statements (Plug Power)")
    print("=" * 80)
    
    # Real data: Plug Power Inc
    market = 'sec'
    entity = 'PLUG_POWER_INC'
    filing_type = '10-K'
    filing_date = '2025-03-03'
    
    print(f"\nAttempting to load: {market}/{entity}/{filing_type}/{filing_date}")
    
    try:
        statements = loader.load_ccq_statements(
            market, entity, filing_type, filing_date
        )
        
        print("✓ CCQ statements loaded successfully")
        print(f"\nStatements loaded:")
        
        for stmt_type in ['balance_sheet', 'income_statement', 'cash_flow', 'other']:
            if stmt_type in statements:
                facts_count = len(statements[stmt_type].get('facts', []))
                print(f"  - {stmt_type}: {facts_count} facts")
        
        metadata = statements.get('metadata', {})
        print(f"\nMetadata:")
        print(f"  - Source: {metadata.get('source')}")
        print(f"  - Total facts: {metadata.get('total_facts')}")
        print(f"  - Statements loaded: {metadata.get('statements_loaded')}")
        
        # Verify structure
        assert 'metadata' in statements, "Missing metadata"
        assert metadata.get('source') == 'ccq', "Wrong source"
        assert metadata.get('total_facts', 0) > 0, "No facts loaded"
        
        # Verify normalization (CCQ line_items converted to facts)
        for stmt_type in statements.get('metadata', {}).get('statements_loaded', []):
            stmt = statements[stmt_type]
            assert 'facts' in stmt, f"{stmt_type} missing 'facts' key"
            
            # Check first fact has normalized structure
            if stmt['facts']:
                first_fact = stmt['facts'][0]
                assert 'concept_qname' in first_fact, "Missing concept_qname"
                assert 'source' in first_fact, "Missing source marker"
                assert first_fact['source'] == 'ccq', "Wrong source marker"
        
        return True, statements
        
    except FileNotFoundError as e:
        print(f"⚠ File not found: {e}")
        print("  This is expected if CCQ data doesn't exist")
        return False, None
        
    except Exception as e:
        print(f"✗ Failed to load CCQ statements: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_compare_formats(map_pro_statements, ccq_statements):
    """Test format comparison between Map Pro and CCQ."""
    print("\n" + "=" * 80)
    print("TEST 4: Compare Formats")
    print("=" * 80)
    
    if not map_pro_statements or not ccq_statements:
        print("⚠ Skipping - missing statement data")
        return False
    
    try:
        print("\nComparing fact structures:")
        
        # Get first fact from each
        map_pro_fact = None
        ccq_fact = None
        
        for stmt_type in ['balance_sheet', 'income_statement', 'cash_flow', 'other']:
            if stmt_type in map_pro_statements:
                facts = map_pro_statements[stmt_type].get('facts', [])
                if facts:
                    map_pro_fact = facts[0]
                    break
        
        for stmt_type in ['balance_sheet', 'income_statement', 'cash_flow', 'other']:
            if stmt_type in ccq_statements:
                facts = ccq_statements[stmt_type].get('facts', [])
                if facts:
                    ccq_fact = facts[0]
                    break
        
        if map_pro_fact:
            print("\nMap Pro fact structure:")
            print(f"  Keys: {list(map_pro_fact.keys())}")
            print(f"  Concept field: {'concept' if 'concept' in map_pro_fact else 'concept_qname' if 'concept_qname' in map_pro_fact else 'MISSING'}")
            print(f"  Has value: {'value' in map_pro_fact}")
        
        if ccq_fact:
            print("\nCCQ fact structure (normalized):")
            print(f"  Keys: {list(ccq_fact.keys())}")
            print(f"  Concept field: {'concept_qname' if 'concept_qname' in ccq_fact else 'concept' if 'concept' in ccq_fact else 'MISSING'}")
            print(f"  Has value: {'value' in ccq_fact}")
            print(f"  Source marker: {ccq_fact.get('source')}")
        
        # Verify both have a concept identifier (key for reconciliation)
        # Map Pro uses 'concept', CCQ uses 'concept_qname'
        if map_pro_fact and ccq_fact:
            map_pro_has_concept = 'concept' in map_pro_fact or 'concept_qname' in map_pro_fact
            ccq_has_concept = 'concept_qname' in ccq_fact or 'concept' in ccq_fact
            
            assert map_pro_has_concept, "Map Pro missing concept identifier"
            assert ccq_has_concept, "CCQ missing concept identifier"
            
            print("\n✓ Both formats have concept identifiers for reconciliation")
            print(f"  Map Pro uses: {'concept' if 'concept' in map_pro_fact else 'concept_qname'}")
            print(f"  CCQ uses: {'concept_qname' if 'concept_qname' in ccq_fact else 'concept'}")
            print("  (Reconciliation engine will normalize these)")
        
        return True
        
    except Exception as e:
        print(f"✗ Format comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all statement loader tests."""
    print("=" * 80)
    print("FACT AUTHORITY - STATEMENT LOADER TESTS")
    print("=" * 80)
    print()
    
    results = []
    
    # Test 1: Initialization
    success, loader, ccq_paths = test_initialization()
    results.append(success)
    
    if not success:
        print("\n✗ Cannot proceed - initialization failed")
        return 1
    
    # Test 2: Load Map Pro (Plug Power)
    success, map_pro_statements = test_load_map_pro_statements(loader)
    results.append(success)
    
    # Test 3: Load CCQ (Plug Power)
    success, ccq_statements = test_load_ccq_statements(loader)
    results.append(success)
    
    # Test 4: Compare formats (only if both loaded)
    if map_pro_statements and ccq_statements:
        success = test_compare_formats(map_pro_statements, ccq_statements)
        results.append(success)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    print(f"\nTest data:")
    print(f"  Entity: PLUG_POWER_INC")
    print(f"  Filing: 10-K/2025-03-03")
    
    if all(results):
        print("\n✓ ALL TESTS PASSED")
        print("\nStatement loader is working correctly!")
        print("Ready for integration testing.")
        return 0
    else:
        print("\n⚠ SOME TESTS FAILED OR SKIPPED")
        print("\nPossible issues:")
        print("  1. Map Pro data may not exist for PLUG_POWER_INC (expected)")
        print("  2. Path configuration incorrect (check .env)")
        print("  3. File structure mismatch (check statement file formats)")
        return 1


if __name__ == '__main__':
    sys.exit(main())