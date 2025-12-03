#!/usr/bin/env python3
"""
Taxonomy Reader Cache Test (Simplified)
========================================

Tests taxonomy_reader with direct path initialization.
Doesn't rely on global ccq_paths to avoid initialization issues.

Usage:
    python3 test_taxonomy_reader_cache_simple.py
"""

import sys
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, '/home/a/Desktop/Stock_software/ccq_val')

from engines.fact_authority.taxonomy_reader import TaxonomyReader, CacheManager


def format_time(seconds: float) -> str:
    """Format time in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    return f"{seconds:.2f}s"


def test_with_cache():
    """Test taxonomy reading with cache."""
    
    print("\n" + "="*70)
    print("TAXONOMY READER + CACHE TEST")
    print("="*70)
    print()
    
    # Direct path setup (bypass global ccq_paths)
    taxonomy_base = Path('/mnt/map_pro/data/taxonomies')
    cache_base = Path('/mnt/map_pro/data/taxonomies/.cache')
    
    print(f"Taxonomy base: {taxonomy_base}")
    print(f"Cache base: {cache_base}")
    print()
    
    # Check parent directory permissions
    print("🔍 Checking permissions...")
    parent_dir = taxonomy_base
    
    if parent_dir.exists():
        import os
        is_writable = os.access(parent_dir, os.W_OK)
        print(f"   Parent directory: {parent_dir}")
        print(f"   Writable: {'✅ Yes' if is_writable else '❌ No'}")
        
        if not is_writable:
            print()
            print("⚠️  WARNING: Parent directory is not writable!")
            print("   Cache creation will likely fail.")
            print("   To fix, run:")
            print(f"     sudo chown -R $USER:$USER {parent_dir}")
            print()
    else:
        print(f"❌ Parent directory does not exist: {parent_dir}")
        return 1
    
    print()
    
    # Test configuration
    taxonomy_name = 'us-gaap'
    version = '2025'
    taxonomy_path = taxonomy_base / 'libraries' / f'{taxonomy_name}-{version}'
    
    # Check taxonomy exists
    if not taxonomy_path.exists():
        print(f"❌ Taxonomy not found: {taxonomy_path}")
        print("   Please check path is correct.")
        return 1
    
    print(f"✅ Taxonomy found: {taxonomy_path}")
    print()
    
    # Initialize components
    print("🔧 Initializing taxonomy reader and cache manager...")
    reader = TaxonomyReader()
    cache_mgr = CacheManager(cache_base)
    print("✅ Initialized")
    print()
    
    # Get cache file path
    cache_file = cache_mgr.get_cache_path(taxonomy_name, version)
    print(f"Cache file will be: {cache_file}")
    print()
    
    # ========================================================================
    # FIRST READ
    # ========================================================================
    
    print("="*70)
    print("FIRST READ")
    print("="*70)
    print()
    
    # Check if cache exists
    if cache_mgr.is_cache_valid(cache_file, taxonomy_path):
        print("ℹ️  Valid cache found, loading from cache...")
        start = time.time()
        profile = cache_mgr.load_profile(cache_file)
        first_time = time.time() - start
        from_cache_first = True
        print(f"✅ Loaded from cache in {format_time(first_time)}")
    else:
        print("ℹ️  No valid cache, reading from taxonomy files...")
        start = time.time()
        profile = reader.read_taxonomy(taxonomy_path)
        first_time = time.time() - start
        from_cache_first = False
        print(f"✅ Read from source in {format_time(first_time)}")
        
        # Save to cache
        print()
        print("💾 Saving to cache...")
        cache_mgr.save_profile(profile, cache_file)
        
        if cache_file.exists():
            size_kb = cache_file.stat().st_size / 1024
            print(f"✅ Cached to {cache_file.name} ({size_kb:.1f} KB)")
        else:
            print("⚠️  Cache file not created (check permissions)")
    
    print()
    
    # Display profile
    print("="*70)
    print("TAXONOMY PROFILE")
    print("="*70)
    print()
    print(f"Name:                  {profile.metadata.get('name', 'unknown')}")
    print(f"Version:               {profile.metadata.get('version', 'unknown')}")
    print(f"Schemas:               {len(profile.structure.get('schema_files', []))}")
    print(f"Presentation linkbases: {len(profile.structure.get('linkbases', {}).get('presentation', []))}")
    print(f"Calculation linkbases:  {len(profile.structure.get('linkbases', {}).get('calculation', []))}")
    print(f"Definition linkbases:   {len(profile.structure.get('linkbases', {}).get('definition', []))}")
    print(f"Label linkbases:        {len(profile.structure.get('linkbases', {}).get('label', []))}")
    print(f"Namespaces:            {len(profile.namespaces)}")
    print(f"Roles:                 {len(profile.roles)}")
    
    statement_types = reader.get_statement_types(profile)
    if statement_types:
        print(f"Statement types:       {', '.join(statement_types)}")
    else:
        print(f"Statement types:       None (metadata taxonomy)")
    
    print()
    
    # ========================================================================
    # SECOND READ (if we just created cache)
    # ========================================================================
    
    if not from_cache_first:
        print("="*70)
        print("SECOND READ (from cache)")
        print("="*70)
        print()
        
        print("ℹ️  Loading from cache...")
        start = time.time()
        profile2 = cache_mgr.load_profile(cache_file)
        second_time = time.time() - start
        
        print(f"✅ Loaded in {format_time(second_time)}")
        print()
        print(f"⚡ SPEEDUP: {first_time/second_time:.1f}x faster!")
        print(f"   First read:  {format_time(first_time)}")
        print(f"   Second read: {format_time(second_time)}")
        print()
    
    # ========================================================================
    # CACHE VERIFICATION
    # ========================================================================
    
    print("="*70)
    print("CACHE VERIFICATION")
    print("="*70)
    print()
    
    cache_info = cache_mgr.get_cache_info()
    
    if cache_info['exists']:
        print(f"✅ Cache directory exists: {cache_info['cache_path']}")
        print(f"✅ Cached profiles: {cache_info['profile_count']}")
        print(f"✅ Total cache size: {cache_info['total_size_mb']:.2f} MB")
        
        if cache_info['profiles']:
            print()
            print("Cached files:")
            for profile_name in cache_info['profiles']:
                print(f"  - {profile_name}")
    else:
        print("⚠️  Cache directory does not exist")
        print("   Cache creation may have failed")
    
    print()
    
    # ========================================================================
    # FILESYSTEM VERIFICATION
    # ========================================================================
    
    print("="*70)
    print("FILESYSTEM VERIFICATION")
    print("="*70)
    print()
    
    print(f"Checking: {cache_base}")
    
    if cache_base.exists():
        print(f"✅ {cache_base} EXISTS")
        
        profiles_dir = cache_base / 'profiles'
        if profiles_dir.exists():
            print(f"✅ {profiles_dir} EXISTS")
            
            cached_files = list(profiles_dir.glob('*.json'))
            print(f"✅ Found {len(cached_files)} cached profile(s)")
            
            for f in cached_files:
                size_kb = f.stat().st_size / 1024
                print(f"   - {f.name} ({size_kb:.1f} KB)")
        else:
            print(f"❌ {profiles_dir} DOES NOT EXIST")
        
        readme = cache_base / 'README.txt'
        if readme.exists():
            print(f"✅ {readme} EXISTS")
        else:
            print(f"⚠️  {readme} DOES NOT EXIST")
    else:
        print(f"❌ {cache_base} DOES NOT EXIST")
        print("   Cache was not created. Possible reasons:")
        print("   - Permission denied")
        print("   - Disk full")
        print("   - Path incorrect")
    
    print()
    
    # ========================================================================
    # COMPLETION
    # ========================================================================
    
    print("="*70)
    print("✅ TEST COMPLETED")
    print("="*70)
    print()
    print("Summary:")
    print(f"  - Taxonomy: {taxonomy_name}-{version}")
    print(f"  - Read time: {format_time(first_time)}")
    print(f"  - Cache created: {'Yes' if cache_file.exists() else 'No'}")
    print(f"  - Cache location: {cache_base}")
    print()
    print("Next steps:")
    print("  1. Run this test again to see cache speedup")
    print("  2. Check cache directory manually:")
    print(f"     ls -lah {cache_base}")
    print("  3. Delete cache anytime (system regenerates):")
    print(f"     rm -rf {cache_base}")
    print()
    
    return 0


def main():
    """Main entry point."""
    try:
        return test_with_cache()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())