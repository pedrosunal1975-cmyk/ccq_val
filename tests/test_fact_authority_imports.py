# File: tests/test_fact_authority_imports.py
# Test: Basic import verification for fact_authority engine
# Run from project root: python tests/test_fact_authority_imports.py

"""
Test Fact Authority Imports
============================

Verifies that all fact_authority components can be imported successfully.

This is the first test to run after deployment to ensure the module
structure is correct.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()


def test_main_orchestrator():
    """Test main orchestrator import."""
    print("Testing main orchestrator import...", end=" ")
    try:
        from engines.fact_authority import FactAuthority
        print("✓ FactAuthority")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_sub_engines():
    """Test sub-engine imports."""
    results = []
    
    print("\nTesting sub-engine imports:")
    
    # Taxonomy Reader
    print("  - TaxonomyReader...", end=" ")
    try:
        from engines.fact_authority import TaxonomyReader
        print("✓")
        results.append(True)
    except Exception as e:
        print(f"✗ FAILED: {e}")
        results.append(False)
    
    # Filings Reader
    print("  - FilingReader...", end=" ")
    try:
        from engines.fact_authority import FilingReader
        print("✓")
        results.append(True)
    except Exception as e:
        print(f"✗ FAILED: {e}")
        results.append(False)
    
    # Facts Reader
    print("  - ParsedFactsLoader...", end=" ")
    try:
        from engines.fact_authority import ParsedFactsLoader
        print("✓")
        results.append(True)
    except Exception as e:
        print(f"✗ FAILED: {e}")
        results.append(False)
    
    return all(results)


def test_input_components():
    """Test input component imports."""
    results = []
    
    print("\nTesting input component imports:")
    
    # Statement Loader
    print("  - StatementLoader...", end=" ")
    try:
        from engines.fact_authority.input import StatementLoader
        print("✓")
        results.append(True)
    except Exception as e:
        print(f"✗ FAILED: {e}")
        results.append(False)
    
    return all(results)


def test_process_components():
    """Test process component imports."""
    results = []
    
    print("\nTesting process component imports:")
    
    components = [
        ('StatementReconciler', 'engines.fact_authority.process'),
        ('StatementClassifier', 'engines.fact_authority.process'),
        ('NullQualityHandler', 'engines.fact_authority.process'),
        ('ExtensionInheritanceTracer', 'engines.fact_authority.process'),
        ('XBRLFilingsConsolidator', 'engines.fact_authority.process'),
    ]
    
    for component_name, module_path in components:
        print(f"  - {component_name}...", end=" ")
        try:
            module = __import__(module_path, fromlist=[component_name])
            getattr(module, component_name)
            print("✓")
            results.append(True)
        except Exception as e:
            print(f"✗ FAILED: {e}")
            results.append(False)
    
    return all(results)


def test_output_components():
    """Test output component imports."""
    results = []
    
    print("\nTesting output component imports:")
    
    # Output Writer
    print("  - OutputWriter...", end=" ")
    try:
        from engines.fact_authority.output import OutputWriter
        print("✓")
        results.append(True)
    except Exception as e:
        print(f"✗ FAILED: {e}")
        results.append(False)
    
    # Reconciliation Reporter
    print("  - ReconciliationReporter...", end=" ")
    try:
        from engines.fact_authority.output import ReconciliationReporter
        print("✓")
        results.append(True)
    except Exception as e:
        print(f"✗ FAILED: {e}")
        results.append(False)
    
    return all(results)


def main():
    """Run all import tests."""
    print("=" * 80)
    print("FACT AUTHORITY - IMPORT VERIFICATION TESTS")
    print("=" * 80)
    
    results = []
    
    # Test main orchestrator
    results.append(test_main_orchestrator())
    
    # Test sub-engines
    results.append(test_sub_engines())
    
    # Test input components
    results.append(test_input_components())
    
    # Test process components
    results.append(test_process_components())
    
    # Test output components
    results.append(test_output_components())
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if all(results):
        print("✓ ALL IMPORTS SUCCESSFUL")
        print("\nNext steps:")
        print("  1. Run component tests: python tests/test_fact_authority_components.py")
        print("  2. Inspect taxonomy structure: python tests/test_taxonomy_reader_output_structure.py")
        return 0
    else:
        print("✗ SOME IMPORTS FAILED")
        print("\nCheck deployment:")
        print("  1. Verify all files copied to correct locations")
        print("  2. Check for missing __init__.py files")
        print("  3. Review error messages above")
        return 1


if __name__ == '__main__':
    sys.exit(main())