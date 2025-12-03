#!/usr/bin/env python3
"""
End-to-End Test: Complete Fact Authority Flow

Tests the ENTIRE pipeline from taxonomy detection through to extension extraction.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engines.fact_authority.filing_taxonomy_detector import FilingTaxonomyDetector
from engines.fact_authority.taxonomy_interface import TaxonomyAuthorityReader

def test_complete_flow():
    """Test the complete end-to-end flow"""
    
    print("=" * 70)
    print("END-TO-END TEST: Complete Fact Authority Flow")
    print("=" * 70)
    
    # Paths
    facts_path = Path('/mnt/map_pro/data/parsed_facts/sec/PLUG_POWER_INC/10-K/2025-03-03/plug-20241231x10k/facts.json')
    taxonomy_base = Path('/mnt/map_pro/data/taxonomies')
    
    print(f"\n1. Testing file existence:")
    print(f"   Facts path: {facts_path}")
    print(f"   Exists: {facts_path.exists()}")
    print(f"   Taxonomy base: {taxonomy_base}")
    print(f"   Exists: {taxonomy_base.exists()}")
    
    if not facts_path.exists():
        print("❌ Facts file not found!")
        return False
    
    # Step 1: Detect taxonomies
    print(f"\n2. STEP 1: Detecting taxonomies...")
    detector = FilingTaxonomyDetector(taxonomy_base_path=taxonomy_base)
    taxonomy_info = detector.detect_from_parsed_facts(facts_path)
    
    print(f"   Standard taxonomy: {taxonomy_info['standard_taxonomy']}-{taxonomy_info['standard_version']}")
    print(f"   Extension namespace: {taxonomy_info.get('extension_namespace')}")
    print(f"   All namespaces: {taxonomy_info['namespaces']}")
    print(f"   Taxonomy paths count: {len(taxonomy_info['taxonomy_paths'])}")
    
    extension_ns = taxonomy_info.get('extension_namespace')
    
    if extension_ns != 'plug':
        print(f"❌ STEP 1 FAILED: Expected extension_namespace='plug', got '{extension_ns}'")
        return False
    else:
        print(f"✅ STEP 1 PASSED: extension_namespace='plug'")
    
    # Step 2: Load taxonomy with extension extraction
    print(f"\n3. STEP 2: Loading taxonomy authority...")
    taxonomy_reader = TaxonomyAuthorityReader()
    
    print(f"   Calling load_filing_taxonomy with:")
    print(f"     - taxonomy_paths: {len(taxonomy_info['taxonomy_paths'])} paths")
    print(f"     - facts_path: {facts_path}")
    print(f"     - extension_namespace: {extension_ns}")
    
    hierarchy = taxonomy_reader.load_filing_taxonomy(
        taxonomy_paths=taxonomy_info['taxonomy_paths'],
        facts_path=facts_path,
        extension_namespace=extension_ns
    )
    
    # Step 3: Check results
    print(f"\n4. STEP 3: Checking loaded taxonomy...")
    total_concepts = len(hierarchy.get('concepts', {}))
    print(f"   Total concepts loaded: {total_concepts}")
    
    # Count extensions (concepts starting with 'plug:')
    extension_count = 0
    for concept_name in hierarchy.get('concepts', {}).keys():
        if concept_name.startswith('plug:'):
            extension_count += 1
    
    print(f"   Extension concepts (plug:*): {extension_count}")
    
    # Sample some extension concepts
    if extension_count > 0:
        sample_extensions = [name for name in hierarchy.get('concepts', {}).keys() 
                           if name.startswith('plug:')][:5]
        print(f"   Sample extensions: {sample_extensions}")
    
    # Step 4: Verdict
    print(f"\n5. FINAL VERDICT:")
    print(f"   Expected: 800-1000 extension concepts")
    print(f"   Actual:   {extension_count} extension concepts")
    
    if extension_count >= 500:
        print(f"✅ TEST PASSED! Extensions were extracted successfully.")
        return True
    elif extension_count > 0:
        print(f"⚠️  PARTIAL SUCCESS: Some extensions loaded but fewer than expected.")
        return False
    else:
        print(f"❌ TEST FAILED! No extensions were extracted.")
        print(f"\n   DEBUGGING INFO:")
        print(f"   - extension_namespace was passed: {extension_ns}")
        print(f"   - facts_path exists: {facts_path.exists()}")
        print(f"   - Total concepts: {total_concepts}")
        print(f"   - This means the extraction code did NOT run!")
        return False


if __name__ == '__main__':
    try:
        success = test_complete_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)