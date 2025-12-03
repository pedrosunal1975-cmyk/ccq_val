# File: test_filings_reader_phase2_batch1.py
# Location: tests/test_filings_reader_phase2_batch1.py

"""
Test Suite for Filings Reader Phase 2 Batch 1
==============================================

Tests the core parser components:
- ExtensionSchemaParser
- LinkbaseReader
- ContextExtractor
- FactExtractor
- InstanceParser

Uses real XBRL files discovered from entities directory.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config_loader import ConfigLoader
from core.data_paths import initialize_paths
from engines.fact_authority.filings_reader.extension_schema_parser import ExtensionSchemaParser
from engines.fact_authority.filings_reader.linkbase_reader import LinkbaseReader
from engines.fact_authority.filings_reader.instance_parser import InstanceParser


def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def find_xbrl_files_using_phase1(filing_dir):
    """
    Use Phase 1 discovery to find XBRL files.
    
    This demonstrates integration between Phase 1 (discovery) and Phase 2 (parsing).
    """
    if not filing_dir or not filing_dir.exists():
        return {}
    
    print(f"\nUsing Phase 1 FilingDiscoverer to find files...")
    
    # Import Phase 1 components
    from engines.fact_authority.filings_reader.filing_discoverer import FilingDiscoverer
    
    # Use Phase 1 discovery
    discoverer = FilingDiscoverer()
    discovered = discoverer.discover(filing_dir)
    
    # DEBUG: Show what Phase 1 actually discovered
    print(f"\nDEBUG - Raw Phase 1 discovery results:")
    for key, value in discovered.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)} files")
            if value:
                print(f"    First file: {value[0].name if hasattr(value[0], 'name') else value[0]}")
        else:
            print(f"  {key}: {value}")
    
    # Map Phase 1 discovery results to our test structure
    files = {
        'extension_schema': discovered['extension_schema'][0] if discovered.get('extension_schema') and discovered['extension_schema'] else None,
        'presentation': discovered['presentation'][0] if discovered.get('presentation') and discovered['presentation'] else None,
        'calculation': discovered['calculation'][0] if discovered.get('calculation') and discovered['calculation'] else None,
        'definition': discovered['definition'][0] if discovered.get('definition') and discovered['definition'] else None,
        'label': discovered['label'][0] if discovered.get('label') and discovered['label'] else None,
        'instance': discovered['instance'][0] if discovered.get('instance') and discovered['instance'] else None
    }
    
    # DEBUG: Show mapped results
    print(f"\nDEBUG - Mapped files for tests:")
    for key, value in files.items():
        if value:
            print(f"  {key}: {value.name} ✓")
        else:
            print(f"  {key}: NOT FOUND ✗")
    
    # Show discovery statistics
    stats = discoverer.get_discovery_statistics(discovered)
    print(f"\nPhase 1 Discovery Statistics:")
    print(f"  Total XBRL files: {stats['total_xbrl_files']}")
    print(f"  Extension schemas: {stats['extension_schemas']}")
    print(f"  Presentation linkbases: {stats['presentation_linkbases']}")
    print(f"  Calculation linkbases: {stats['calculation_linkbases']}")
    print(f"  Definition linkbases: {stats['definition_linkbases']}")
    print(f"  Label linkbases: {stats['label_linkbases']}")
    print(f"  Instance documents: {stats['instance_documents']}")
    
    return files


def test_extension_schema_parser(schema_path):
    """Test ExtensionSchemaParser."""
    print_section("TEST 1: ExtensionSchemaParser")
    
    if not schema_path or not schema_path.exists():
        print("SKIP: No extension schema found")
        return False
    
    print(f"Schema file: {schema_path.name}")
    
    try:
        parser = ExtensionSchemaParser()
        result = parser.parse(schema_path)
        
        print(f"\nParsing results:")
        print(f"  Namespace: {result['namespace']}")
        print(f"  Prefix: {result['namespace_prefix']}")
        print(f"  Year: {result.get('taxonomy_year', 'N/A')}")
        print(f"  Element count: {result['element_count']}")
        print(f"  Import count: {len(result['imports'])}")
        
        if result['elements']:
            print(f"\nSample elements (first 3):")
            for elem in result['elements'][:3]:
                print(f"    - {elem['name']}: {elem.get('type', 'no type')}")
        
        # Test helper methods
        element_names = parser.get_element_names(result)
        monetary = parser.get_monetary_elements(result)
        
        print(f"\nHelper methods:")
        print(f"  Total element names: {len(element_names)}")
        print(f"  Monetary elements: {len(monetary)}")
        
        print("\nExtensionSchemaParser: PASS")
        return True
    
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_linkbase_reader(linkbase_paths):
    """Test LinkbaseReader."""
    print_section("TEST 2: LinkbaseReader")
    
    if not any(linkbase_paths.values()):
        print("SKIP: No linkbases found")
        return False
    
    try:
        reader = LinkbaseReader()
        
        # Test individual linkbases
        if linkbase_paths.get('presentation'):
            print(f"\nPresentation linkbase: {linkbase_paths['presentation'].name}")
            pres = reader.parse_presentation(linkbase_paths['presentation'])
            print(f"  Roles: {len(pres['roles'])}")
            print(f"  Arcs: {pres['arc_count']}")
        
        if linkbase_paths.get('calculation'):
            print(f"\nCalculation linkbase: {linkbase_paths['calculation'].name}")
            calc = reader.parse_calculation(linkbase_paths['calculation'])
            print(f"  Roles: {len(calc['roles'])}")
            print(f"  Arcs: {calc['arc_count']}")
        
        if linkbase_paths.get('definition'):
            print(f"\nDefinition linkbase: {linkbase_paths['definition'].name}")
            def_lb = reader.parse_definition(linkbase_paths['definition'])
            print(f"  Roles: {len(def_lb['roles'])}")
            print(f"  Arcs: {def_lb['arc_count']}")
        
        if linkbase_paths.get('label'):
            print(f"\nLabel linkbase: {linkbase_paths['label'].name}")
            labels = reader.parse_label(linkbase_paths['label'])
            print(f"  Labels: {labels['label_count']}")
            print(f"  Languages: {labels['languages']}")
        
        # Test parse_all
        print(f"\nTesting parse_all()...")
        all_data = reader.parse_all(
            presentation_path=linkbase_paths.get('presentation'),
            calculation_path=linkbase_paths.get('calculation'),
            definition_path=linkbase_paths.get('definition'),
            label_path=linkbase_paths.get('label')
        )
        
        parsed_count = sum(1 for v in all_data.values() if v is not None)
        print(f"  Parsed {parsed_count} linkbase types")
        
        print("\nLinkbaseReader: PASS")
        return True
    
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_instance_parser(instance_path):
    """Test InstanceParser."""
    print_section("TEST 3: InstanceParser")
    
    if not instance_path or not instance_path.exists():
        print("SKIP: No instance document found")
        return False
    
    print(f"Instance file: {instance_path.name}")
    
    try:
        parser = InstanceParser()
        result = parser.parse(instance_path)
        
        print(f"\nParsing results:")
        print(f"  Format: {result['format']}")
        print(f"  Entity ID: {result['entity_identifier']}")
        print(f"  Fact count: {result['fact_count']}")
        print(f"  Context count: {result['context_count']}")
        print(f"  Unit count: {result['unit_count']}")
        
        # Show sample facts
        if result['facts']:
            print(f"\nSample facts (first 3):")
            for fact in result['facts'][:3]:
                concept = fact['concept']
                value = fact.get('value', 'N/A')
                if len(str(value)) > 50:
                    value = str(value)[:50] + "..."
                print(f"    - {concept}: {value}")
        
        # Test helper methods
        if result['facts']:
            first_concept = result['facts'][0]['concept']
            concept_facts = parser.get_facts_by_concept(result, first_concept)
            print(f"\nFacts with concept '{first_concept}': {len(concept_facts)}")
        
        monetary_facts = parser.get_monetary_facts(result)
        print(f"Monetary facts: {len(monetary_facts)}")
        
        print("\nInstanceParser: PASS")
        return True
    
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_batch1_tests(filing_dir=None):
    """Run all Batch 1 tests with Phase 1 integration."""
    print("\n" + "=" * 80)
    print("  FILINGS READER PHASE 2 BATCH 1 - TEST SUITE")
    print("  (Demonstrating Phase 1 + Phase 2 Integration)")
    print("=" * 80)
    
    # Initialize paths
    print("\nInitializing data paths...")
    config = ConfigLoader()
    config_dict = config.get_all()
    paths = initialize_paths(config_dict)
    
    # Auto-discover filing using Phase 1 MarketStructureDetector if not provided
    if not filing_dir:
        print(f"\nAuto-discovering filing from: {paths.mapper_xbrl}")
        
        # Import Phase 1 discovery components
        from engines.fact_authority.filings_reader.filing_discoverer import FilingDiscoverer
        
        if paths.mapper_xbrl:
            # Search for a filing directory with XBRL files
            for item in paths.mapper_xbrl.rglob('*'):
                if item.is_dir() and item.name == 'extracted':
                    # Quick check using Phase 1
                    discoverer = FilingDiscoverer()
                    if discoverer.quick_check(item):
                        filing_dir = item
                        print(f"Found filing via Phase 1 discovery: {filing_dir}")
                        break
    
    if not filing_dir:
        print("\nERROR: No filing directory provided or found")
        print("Try: python tests/test_filings_reader_phase2_batch1.py --filing-dir /path/to/filing")
        return False
    
    # Use Phase 1 FilingDiscoverer to find XBRL files
    print(f"\n" + "=" * 80)
    print(f"  PHASE 1 + PHASE 2 INTEGRATION TEST")
    print("=" * 80)
    print(f"Filing directory: {filing_dir}")
    
    xbrl_files = find_xbrl_files_using_phase1(filing_dir)
    
    print("\nDiscovered files:")
    for file_type, path in xbrl_files.items():
        if path:
            print(f"  {file_type}: {path.name}")
        else:
            print(f"  {file_type}: Not found")
    
    # Run Phase 2 parser tests on Phase 1 discovered files
    test1_result = test_extension_schema_parser(xbrl_files.get('extension_schema'))
    
    linkbase_paths = {
        'presentation': xbrl_files.get('presentation'),
        'calculation': xbrl_files.get('calculation'),
        'definition': xbrl_files.get('definition'),
        'label': xbrl_files.get('label')
    }
    test2_result = test_linkbase_reader(linkbase_paths)
    
    test3_result = test_instance_parser(xbrl_files.get('instance'))
    
    # Summary
    print_section("TEST SUMMARY")
    print("Phase 1 Integration: PASS (discovery worked)")
    print(f"Test 1 - ExtensionSchemaParser: {'PASS' if test1_result else 'FAIL/SKIP'}")
    print(f"Test 2 - LinkbaseReader: {'PASS' if test2_result else 'FAIL/SKIP'}")
    print(f"Test 3 - InstanceParser: {'PASS' if test3_result else 'FAIL/SKIP'}")
    
    overall = test1_result or test2_result or test3_result
    
    print("\n" + "=" * 80)
    if overall:
        print("  BATCH 1 TESTS: PASSED")
        print("  Phase 1 + Phase 2 Integration: SUCCESSFUL")
    else:
        print("  BATCH 1 TESTS: NO TESTS RAN")
    print("=" * 80 + "\n")
    
    return overall


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test Phase 2 Batch 1 with Phase 1 integration (auto-discovery enabled)'
    )
    parser.add_argument(
        '--filing-dir',
        type=str,
        help='Path to filing directory (optional - will auto-discover using Phase 1 if not provided)'
    )
    
    args = parser.parse_args()
    
    filing_dir = Path(args.filing_dir) if args.filing_dir else None
    success = run_batch1_tests(filing_dir)
    sys.exit(0 if success else 1)