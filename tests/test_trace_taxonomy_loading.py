#!/usr/bin/env python3
"""
Test: Complete Taxonomy Loading Trace
======================================

Traces the entire taxonomy loading process with detailed logging.

Run from ccq_val root:
    python3 tests/test_trace_taxonomy_loading.py
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
from engines.fact_authority.filing_taxonomy_detector import FilingTaxonomyDetector
from engines.ccq_mapper.loaders.taxonomy_loader import TaxonomyLoader


def test_complete_flow():
    """Trace the complete taxonomy loading flow."""
    
    print("=" * 70)
    print("COMPLETE TAXONOMY LOADING TRACE")
    print("=" * 70)
    
    # Step 1: Initialize paths
    print("\n[STEP 1] Initialize paths")
    print("-" * 70)
    
    config = ConfigLoader()
    paths = initialize_paths(config._config)
    
    print(f"Taxonomy base: {paths.taxonomies}")
    print(f"Exists: {paths.taxonomies.exists()}")
    
    # Step 2: Use detector to find taxonomy paths
    print("\n[STEP 2] Use FilingTaxonomyDetector to find paths")
    print("-" * 70)
    
    detector = FilingTaxonomyDetector(taxonomy_base_path=paths.taxonomies)
    
    # Manually build the search path like the detector does
    taxonomy = 'us-gaap'
    version = '2024'
    
    base_search_path = paths.taxonomies / 'libraries' / f"{taxonomy}-{version}"
    print(f"Search path: {base_search_path}")
    print(f"Exists: {base_search_path.exists()}")
    
    # Use detector's method
    taxonomy_dir = detector._find_taxonomy_files_directory(base_search_path, taxonomy)
    
    print(f"\nDetector returned: {taxonomy_dir}")
    
    if taxonomy_dir:
        print(f"Directory exists: {taxonomy_dir.exists()}")
        
        # Count XSD files
        xsd_files = list(taxonomy_dir.glob('*.xsd'))
        print(f"XSD files in directory: {len(xsd_files)}")
        
        if xsd_files:
            print(f"\nFirst 5 XSD files:")
            for i, xsd in enumerate(xsd_files[:5]):
                print(f"  {i+1}. {xsd.name}")
    
    # Step 3: Use TaxonomyLoader to load from that path
    print("\n[STEP 3] Use TaxonomyLoader to load concepts")
    print("-" * 70)
    
    if not taxonomy_dir:
        print("ERROR: No taxonomy directory found!")
        return
    
    loader = TaxonomyLoader()
    
    print(f"Loading from: {taxonomy_dir}")
    
    # Load taxonomies
    taxonomy_data = loader.load_taxonomies([taxonomy_dir])
    
    concepts_count = len(taxonomy_data.get('concepts', {}))
    labels_count = len(taxonomy_data.get('labels', {}))
    
    print(f"\nResults:")
    print(f"  Concepts loaded: {concepts_count}")
    print(f"  Labels loaded: {labels_count}")
    
    if concepts_count > 0:
        print(f"\n✓ SUCCESS! Loaded {concepts_count} concepts")
        
        # Show first 5 concepts
        concepts = taxonomy_data['concepts']
        print(f"\nFirst 5 concepts:")
        for i, (qname, data) in enumerate(list(concepts.items())[:5]):
            print(f"  {i+1}. {qname}")
            print(f"     balance: {data.get('balance_type', 'none')}")
            print(f"     period: {data.get('period_type', 'none')}")
    else:
        print(f"\n✗ FAILED: No concepts loaded")
        
        # Debug: Manually try to load one file
        print("\n[DEBUG] Manually testing with one file")
        print("-" * 70)
        
        xsd_files = list(taxonomy_dir.glob('*.xsd'))
        if xsd_files:
            test_file = xsd_files[0]
            print(f"Testing file: {test_file.name}")
            
            import xml.etree.ElementTree as ET
            
            try:
                tree = ET.parse(test_file)
                root = tree.getroot()
                
                NAMESPACES = {
                    'xsd': 'http://www.w3.org/2001/XMLSchema',
                }
                
                elements = root.findall('.//xsd:element', NAMESPACES)
                print(f"Elements found in file: {len(elements)}")
                
                if elements:
                    print("First element:")
                    elem = elements[0]
                    print(f"  name: {elem.get('name')}")
                    print(f"  type: {elem.get('type')}")
                    
                    # Try to parse it like TaxonomyLoader does
                    name = elem.get('name')
                    if name:
                        print(f"\n✓ Element parsing works")
                    else:
                        print(f"\n✗ Element has no name attribute")
                else:
                    print("No elements found - file might be empty/linkbase")
                    
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()


if __name__ == '__main__':
    test_complete_flow()