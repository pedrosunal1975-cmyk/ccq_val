#!/usr/bin/env python3
"""
View CCQ Mapper Database Content
=================================

Display all data from mapper-related tables.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database_coordinator import DatabaseCoordinator
from sqlalchemy import text
import json

def view_mapper_database():
    """View all mapper-related data."""
    db = DatabaseCoordinator()
    
    print("=" * 80)
    print("CCQ MAPPER DATABASE CONTENT")
    print("=" * 80)
    
    with db.get_session() as session:
        # 1. Mapper Jobs
        print("\n[MAPPER JOBS]")
        print("-" * 80)
        result = session.execute(text("""
            SELECT job_id, filing_id, company_name, filing_type, filing_date, 
                   market, status, created_at, last_error
            FROM mapper_jobs
            ORDER BY created_at DESC
        """))
        jobs = result.fetchall()
        
        if jobs:
            for job in jobs:
                print(f"\nJob ID: {job[0]}")
                print(f"  Filing ID: {job[1]}")
                print(f"  Company: {job[2]}")
                print(f"  Type: {job[3]} | Date: {job[4]}")
                print(f"  Market: {job[5]}")
                print(f"  Status: {job[6]}")
                print(f"  Created: {job[7]}")
                if job[8]:
                    print(f"  Error: {job[8]}")
        else:
            print("  (no jobs found)")
        
        # 2. Mapping Results
        print("\n\n[MAPPING RESULTS]")
        print("-" * 80)
        result = session.execute(text("""
            SELECT result_id, job_id, filing_id, company_name, 
                   output_directory, statistics, mapped_at
            FROM mapping_results
            ORDER BY mapped_at DESC
        """))
        results = result.fetchall()
        
        if results:
            for res in results:
                print(f"\nResult ID: {res[0]}")
                print(f"  Job ID: {res[1]}")
                print(f"  Filing ID: {res[2]}")
                print(f"  Company: {res[3]}")
                print(f"  Output: {res[4]}")
                if res[5]:
                    stats = res[5] if isinstance(res[5], dict) else {}
                    print(f"  Statistics: {json.dumps(stats, indent=4, default=str)}")
                print(f"  Mapped: {res[6]}")
        else:
            print("  (no results found)")
        
        # 3. Comparison Results
        print("\n\n[COMPARISON RESULTS]")
        print("-" * 80)
        result = session.execute(text("""
            SELECT comparison_id, result_id, filing_id, 
                   agreement_rate, created_at
            FROM comparison_results
            ORDER BY created_at DESC
        """))
        comparisons = result.fetchall()
        
        if comparisons:
            for comp in comparisons:
                print(f"\nComparison ID: {comp[0]}")
                print(f"  Result ID: {comp[1]}")
                print(f"  Filing ID: {comp[2]}")
                print(f"  Agreement Rate: {comp[3]}")
                print(f"  Created: {comp[4]}")
        else:
            print("  (no comparisons found)")
        
        # Summary counts
        print("\n\n[SUMMARY]")
        print("-" * 80)
        job_count = session.execute(text("SELECT COUNT(*) FROM mapper_jobs")).scalar()
        result_count = session.execute(text("SELECT COUNT(*) FROM mapping_results")).scalar()
        comp_count = session.execute(text("SELECT COUNT(*) FROM comparison_results")).scalar()
        
        print(f"Total Jobs: {job_count}")
        print(f"Total Results: {result_count}")
        print(f"Total Comparisons: {comp_count}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    view_mapper_database()