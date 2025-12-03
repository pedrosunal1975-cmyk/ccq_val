"""
Test Suite for Facts Reader Sub-Engine

Tests the facts_reader components:
- ParsedFactsLoader: Loading parsed facts from Map Pro
- FactsValidator: Validating facts structure and content

Demonstrates integration with existing CCQPaths infrastructure.
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


def test_parsed_facts_loader(ccq_paths):
    """
    Test ParsedFactsLoader with auto-discovery.
    
    Args:
        ccq_paths: CCQPaths instance
        
    Returns:
        Loaded facts_data if successful, None otherwise
    """
    print_section("TEST 1: ParsedFactsLoader")
    
    from engines.fact_authority.facts_reader import ParsedFactsLoader
    
    loader = ParsedFactsLoader(ccq_paths)
    
    # PROPER DIAGNOSTIC: Check if path exists
    print(f"\nConfigured parsed facts path: {ccq_paths.parsed_facts}")
    
    if not ccq_paths.parsed_facts.exists():
        print(f"\nDIAGNOSTIC FAILURE:")
        print(f"  Directory does not exist: {ccq_paths.parsed_facts}")
        print(f"\nThis means one of:")
        print(f"  1. Map Pro has not been run yet to create parsed facts")
        print(f"  2. The .env configuration path is incorrect")
        print(f"  3. Map Pro stores parsed facts in database only (not JSON files)")
        print(f"\nTo fix:")
        print(f"  - Check .env: CCQ_PARSED_FACTS_PATH={ccq_paths.parsed_facts}")
        print(f"  - Verify Map Pro has run and created parsed facts")
        print(f"  - Create directory: mkdir -p {ccq_paths.parsed_facts}")
        print("\nParsedFactsLoader: SKIP (directory doesn't exist)")
        return None
    
    # Directory exists, search for files
    print(f"  Directory exists: YES")
    
    # Show what's actually in the directory
    all_files = list(ccq_paths.parsed_facts.rglob('*'))
    print(f"  Total items in directory tree: {len(all_files)}")
    
    if all_files:
        print(f"\n  Sample of files found:")
        for item in all_files[:10]:
            if item.is_file():
                print(f"    {item.relative_to(ccq_paths.parsed_facts)}")
    
    # Look for JSON files with various patterns
    patterns = [
        'parsed_facts*.json',
        '*.json',
        'facts*.json',
        'parsed*.json'
    ]
    
    facts_file = None
    for pattern in patterns:
        matches = list(ccq_paths.parsed_facts.rglob(pattern))
        if matches:
            facts_file = matches[0]
            print(f"\n  Found JSON using pattern '{pattern}': {facts_file.name}")
            break
        else:
            print(f"  Pattern '{pattern}': 0 matches")
    
    if not facts_file:
        print(f"\nDIAGNOSTIC FAILURE:")
        print(f"  No JSON files found in {ccq_paths.parsed_facts}")
        print(f"  Directory exists but is empty or contains no JSON files")
        print("\nParsedFactsLoader: SKIP (no JSON files found)")
        return None
    
    try:
        # Load facts
        print(f"\nLoading: {facts_file.name}")
        print(f"  Full path: {facts_file}")
        facts_data = loader.load_from_path(facts_file)
        
        # Get statistics
        stats = loader.get_statistics(facts_data)
        print(f"\nLoading results:")
        print(f"  Total facts: {stats['total_facts']}")
        print(f"  Total contexts: {stats['total_contexts']}")
        print(f"  Total units: {stats['total_units']}")
        print(f"  Has metadata: {stats['has_metadata']}")
        print(f"  Has contexts: {stats['has_contexts']}")
        print(f"  Has units: {stats['has_units']}")
        print(f"  Market: {stats['market']}")
        print(f"  Company: {stats['company']}")
        print(f"  Filing type: {stats['filing_type']}")
        
        # Get metadata
        metadata = loader.get_metadata(facts_data)
        if metadata:
            print(f"\nMetadata:")
            for key, value in list(metadata.items())[:5]:
                print(f"  {key}: {value}")
        
        # Test filtering with fallback pattern
        facts = loader.get_facts(facts_data)
        if facts:
            # Get first concept using fallback pattern
            first_fact = facts[0]
            first_concept = (
                first_fact.get('concept_qname') or
                first_fact.get('qname') or
                first_fact.get('concept')
            )
            
            if first_concept:
                filtered = loader.filter_facts_by_concept(facts_data, first_concept)
                print(f"\nFiltering test:")
                print(f"  Facts with concept '{first_concept}': {len(filtered)}")
            else:
                print(f"\nFiltering test:")
                print(f"  ERROR: First fact has no concept field!")
        
        # Show actual field names detected
        if facts:
            first_fact = facts[0]
            print(f"\nFirst fact structure (sample fields):")
            
            # Concept fields
            if 'concept_qname' in first_fact:
                print(f"  concept_qname: {first_fact['concept_qname']}")
            elif 'qname' in first_fact:
                print(f"  qname: {first_fact['qname']}")
            
            # Value fields  
            if 'fact_value' in first_fact:
                print(f"  fact_value: {first_fact['fact_value']}")
            elif 'value' in first_fact:
                print(f"  value: {first_fact['value']}")
            
            # Context fields
            if 'context_ref' in first_fact:
                print(f"  context_ref: {first_fact['context_ref']}")
            elif 'contextRef' in first_fact:
                print(f"  contextRef: {first_fact['contextRef']}")
            
            # Unit fields
            if 'unit_ref' in first_fact:
                print(f"  unit_ref: {first_fact['unit_ref']}")
            elif 'unit' in first_fact:
                print(f"  unit: {first_fact['unit']}")
        
        print("\nParsedFactsLoader: PASS")
        return facts_data
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\nParsedFactsLoader: FAIL")
        return None


def test_facts_validator(facts_data):
    """
    Test FactsValidator with loaded facts.
    
    Args:
        facts_data: Loaded facts data from ParsedFactsLoader
        
    Returns:
        True if test passed
    """
    print_section("TEST 2: FactsValidator")
    
    if not facts_data:
        print("SKIP: No facts data to validate")
        return False
    
    from engines.fact_authority.facts_reader import FactsValidator
    
    validator = FactsValidator()
    
    try:
        # Validate facts
        print("Validating parsed facts...")
        validation = validator.validate(facts_data)
        
        print(f"\nValidation results:")
        print(f"  Valid: {validation['is_valid']}")
        print(f"  Errors: {len(validation['errors'])}")
        print(f"  Warnings: {len(validation['warnings'])}")
        
        if validation['errors']:
            print(f"\n  Error details:")
            for error in validation['errors'][:5]:
                print(f"    - {error}")
        
        if validation['warnings']:
            print(f"\n  Warning details:")
            for warning in validation['warnings'][:5]:
                print(f"    - {warning}")
        
        # Statistics
        stats = validation['statistics']
        print(f"\nStatistics:")
        print(f"  Total facts: {stats.get('total_facts', 0)}")
        print(f"  Unique concepts: {stats.get('unique_concepts', 0)}")
        print(f"  Unique contexts: {stats.get('unique_contexts', 0)}")
        print(f"  Facts with units: {stats.get('facts_with_units', 0)}")
        print(f"  Null values: {stats.get('null_values', 0)}")
        
        # Completeness
        completeness = validation['completeness']
        print(f"\nCompleteness:")
        print(f"  Required fields: {completeness.get('required_fields', 0):.1f}%")
        print(f"  Common fields: {completeness.get('common_fields', 0):.1f}%")
        print(f"  Complete facts: {completeness.get('complete_facts', 0)}")
        
        print("\nFactsValidator: PASS")
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\nFactsValidator: FAIL")
        return False


def test_loading_by_filing_info(ccq_paths):
    """
    Test loading facts by filing information.
    
    Uses the actual filing we found in test 1.
    
    Args:
        ccq_paths: CCQPaths instance
        
    Returns:
        True if test passed
    """
    print_section("TEST 3: Load by Filing Info")
    
    from engines.fact_authority.facts_reader import ParsedFactsLoader
    
    loader = ParsedFactsLoader(ccq_paths)
    
    # Use the actual filing we found in Test 1
    print("Testing load_by_filing_info() with real filing:")
    print("  Market: sec")
    print("  Entity: Albertsons_Companies__Inc_")
    print("  Filing type: 10-K")
    print("  Date: 2025-04-21")
    
    try:
        facts_data = loader.load_by_filing_info(
            market='sec',
            entity_name='Albertsons_Companies__Inc_',
            filing_type='10-K',
            filing_date='2025-04-21'
        )
        
        facts = loader.get_facts(facts_data)
        metadata = loader.get_metadata(facts_data)
        
        print(f"\nSuccessfully loaded:")
        print(f"  Facts: {len(facts)}")
        print(f"  Company: {metadata.get('company', 'N/A')}")
        print(f"  Market: {metadata.get('market', 'N/A')}")
        
        print("\nLoad by Filing Info: PASS")
        return True
        
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("\nLoad by Filing Info: FAIL")
        return False
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\nLoad by Filing Info: FAIL")
        return False


def run_facts_reader_tests():
    """Run all facts_reader tests."""
    print("\n" + "=" * 80)
    print("  FACTS READER SUB-ENGINE - TEST SUITE")
    print("  (Parsed Facts Loader for Fact Authority)")
    print("=" * 80)
    
    # Initialize paths
    print("\nInitializing data paths...")
    config = ConfigLoader()
    config_dict = config.get_all()
    ccq_paths = initialize_paths(config_dict)
    
    print(f"Parsed facts directory: {ccq_paths.parsed_facts}")
    
    # Test ParsedFactsLoader
    facts_data = test_parsed_facts_loader(ccq_paths)
    test1_result = facts_data is not None
    
    # Test FactsValidator
    test2_result = test_facts_validator(facts_data)
    
    # Test loading by filing info
    test3_result = test_loading_by_filing_info(ccq_paths)
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"Test 1 - ParsedFactsLoader: {'PASS' if test1_result else 'FAIL/SKIP'}")
    print(f"Test 2 - FactsValidator: {'PASS' if test2_result else 'FAIL/SKIP'}")
    print(f"Test 3 - Load by Filing Info: {'PASS' if test3_result else 'FAIL'}")
    
    overall = test1_result and test2_result and test3_result
    
    print("\n" + "=" * 80)
    if overall:
        print("  FACTS READER TESTS: PASSED")
        print("  Facts Reader Sub-Engine: Ready for production")
    else:
        print("  FACTS READER TESTS: PARTIAL/SKIP")
        print("  (May need parsed facts files to test fully)")
    print("=" * 80 + "\n")
    
    return overall


if __name__ == '__main__':
    success = run_facts_reader_tests()
    sys.exit(0 if success else 1)