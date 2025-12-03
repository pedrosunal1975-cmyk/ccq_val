#!/usr/bin/env python3
"""
Test: Diagnose Extension Namespace Detection

This test verifies that the extension namespace detection logic correctly
identifies 'plug' as the company extension and not 'cyd' (which is a 
standard taxonomy).
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engines.fact_authority.taxonomy_constants import (
    STANDARD_TAXONOMIES, 
    METADATA_TAXONOMIES,
    NON_TAXONOMY_NAMESPACES
)


def test_extension_detection():
    """Test that extension namespace detection works correctly"""
    
    print("=" * 70)
    print("DIAGNOSTIC: Extension Namespace Detection")
    print("=" * 70)
    
    # Check what's in the constants
    print("\n1. METADATA_TAXONOMIES contains:")
    for key in sorted(METADATA_TAXONOMIES.keys()):
        print(f"   - {key}")
    
    print(f"\n2. Is 'cyd' in METADATA_TAXONOMIES? {('cyd' in METADATA_TAXONOMIES)}")
    print(f"3. Is 'cyd' in STANDARD_TAXONOMIES? {('cyd' in STANDARD_TAXONOMIES)}")
    print(f"4. Is 'plug' in STANDARD_TAXONOMIES? {('plug' in STANDARD_TAXONOMIES)}")
    
    # Simulate what _find_extension_namespace does
    namespaces = ['cyd', 'dei', 'ecd', 'plug', 'us-gaap']
    print(f"\n5. Input namespaces: {namespaces}")
    
    extension_candidates = []
    print("\n6. Processing each namespace:")
    for ns in namespaces:
        in_standard = ns in STANDARD_TAXONOMIES
        in_non_taxonomy = ns in NON_TAXONOMY_NAMESPACES
        
        if in_standard:
            status = "SKIP (standard taxonomy)"
        elif in_non_taxonomy:
            status = "SKIP (non-taxonomy namespace)"
        else:
            status = "ADD (company extension)"
            extension_candidates.append(ns)
        
        print(f"   - {ns:15s} → {status}")
    
    selected = extension_candidates[0] if extension_candidates else None
    
    print(f"\n7. Extension candidates found: {extension_candidates}")
    print(f"8. Selected extension namespace: {selected}")
    
    print("\n" + "=" * 70)
    print("EXPECTED RESULT:")
    print("  - 'cyd' should be SKIPPED (it's a standard taxonomy)")
    print("  - 'plug' should be SELECTED (it's the company extension)")
    print(f"\nACTUAL RESULT: {selected}")
    
    if selected == 'plug':
        print("✅ TEST PASSED!")
        return True
    else:
        print(f"❌ TEST FAILED! Expected 'plug' but got '{selected}'")
        return False


if __name__ == '__main__':
    success = test_extension_detection()
    sys.exit(0 if success else 1)