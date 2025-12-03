#!/usr/bin/env python3
"""
CCQ Mapper Database Initialization
===================================

Helper script to initialize or verify CCQ Mapper database tables.

Usage:
    python init_mapper_db.py --check          # Check if tables exist
    python init_mapper_db.py --init           # Initialize tables
    python init_mapper_db.py --test           # Run test operations
"""

import argparse
import sys
from pathlib import Path

from sqlalchemy import inspect, text

from core.database_coordinator import DatabaseCoordinator
from core.system_logger import get_logger
from database import Base
from database.models.mapper_models import (
    MapperJob, MappingResult, MapProComparison, MapperStatistics
)

logger = get_logger(__name__)


class MapperDatabaseInitializer:
    """Initialize and verify CCQ Mapper database."""
    
    def __init__(self):
        """Initialize database coordinator."""
        self.db = DatabaseCoordinator()
        logger.info("Database coordinator initialized")
    
    def check_tables(self) -> dict:
        """
        Check if mapper tables exist.
        
        Returns:
            Dictionary with table existence status
        """
        logger.info("Checking mapper tables...")
        
        inspector = inspect(self.db._engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = {
            'mapper_jobs': MapperJob.__tablename__,
            'mapping_results': MappingResult.__tablename__,
            'map_pro_comparisons': MapProComparison.__tablename__,
            'mapper_statistics': MapperStatistics.__tablename__
        }
        
        status = {}
        for name, table_name in required_tables.items():
            exists = table_name in existing_tables
            status[name] = exists
            
            if exists:
                logger.info(f"✓ {name} exists")
            else:
                logger.warning(f"✗ {name} missing")
        
        return status
    
    def check_views(self) -> dict:
        """
        Check if mapper views exist.
        
        Returns:
            Dictionary with view existence status
        """
        logger.info("Checking mapper views...")
        
        required_views = [
            'recent_mapper_jobs',
            'validated_mappings',
            'mapper_disagreements',
            'mapper_performance'
        ]
        
        status = {}
        
        with self.db.get_session() as session:
            for view_name in required_views:
                try:
                    result = session.execute(
                        text(f"SELECT 1 FROM {view_name} LIMIT 0")
                    )
                    status[view_name] = True
                    logger.info(f"✓ {view_name} exists")
                except Exception as e:
                    status[view_name] = False
                    logger.warning(f"✗ {view_name} missing: {e}")
        
        return status
    
    def initialize_tables(self):
        """
        Initialize mapper tables using SQLAlchemy.
        
        Note: This creates tables programmatically.
        For production, use the SQL migration script instead.
        """
        logger.info("Initializing mapper tables...")
        
        try:
            # Create all tables
            Base.metadata.create_all(
                self.db._engine,
                tables=[
                    MapperJob.__table__,
                    MappingResult.__table__,
                    MapProComparison.__table__,
                    MapperStatistics.__table__
                ]
            )
            
            logger.info("✓ Tables created successfully")
            
            # Note: Views and functions must be created via SQL migration
            logger.warning(
                "⚠ Views and functions not created. "
                "Run add_mapper_tables.sql for complete setup."
            )
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def run_tests(self):
        """Run basic database tests."""
        logger.info("Running database tests...")
        
        # Test 1: Connection
        logger.info("Test 1: Testing connection...")
        if not self.db.test_connection():
            raise Exception("Database connection test failed")
        logger.info("✓ Connection test passed")
        
        # Test 2: Tables exist
        logger.info("Test 2: Checking tables...")
        table_status = self.check_tables()
        if not all(table_status.values()):
            raise Exception(f"Missing tables: {[k for k, v in table_status.items() if not v]}")
        logger.info("✓ All tables exist")
        
        # Test 3: Views exist
        logger.info("Test 3: Checking views...")
        view_status = self.check_views()
        if not all(view_status.values()):
            logger.warning(f"Missing views: {[k for k, v in view_status.items() if not v]}")
            logger.warning("Run add_mapper_tables.sql to create views")
        else:
            logger.info("✓ All views exist")
        
        # Test 4: Insert test job
        logger.info("Test 4: Testing job creation...")
        from database import create_mapper_job
        from datetime import date
        
        with self.db.get_session() as session:
            test_job = create_mapper_job(
                session,
                filing_id='TEST_INIT_001',
                company_name='Test Company',
                filing_type='10-K',
                filing_date=date.today(),
                market='sec',
                xbrl_path='/test/path.xml',
                parsed_facts_path='/test/facts.json',
                taxonomy_paths=['/test/taxonomy']
            )
            
            job_id = test_job.job_id
            logger.info(f"✓ Test job created: {job_id}")
            
            # Clean up
            session.delete(test_job)
            session.commit()
            logger.info("✓ Test job cleaned up")
        
        # Test 5: Query operations
        logger.info("Test 5: Testing queries...")
        from database import get_pending_mapper_jobs
        
        with self.db.get_session() as session:
            pending = get_pending_mapper_jobs(session, limit=1)
            logger.info(f"✓ Query test passed (found {len(pending)} pending jobs)")
        
        logger.info("=" * 60)
        logger.info("All tests passed successfully!")
        logger.info("=" * 60)
    
    def get_statistics(self):
        """Get database statistics."""
        logger.info("Getting database statistics...")
        
        with self.db.get_session() as session:
            # Count jobs
            job_count = session.execute(
                text("SELECT COUNT(*) FROM mapper_jobs")
            ).scalar()
            
            # Count results
            result_count = session.execute(
                text("SELECT COUNT(*) FROM mapping_results")
            ).scalar()
            
            # Count comparisons
            comparison_count = session.execute(
                text("SELECT COUNT(*) FROM map_pro_comparisons")
            ).scalar()
            
            # Status breakdown
            status_counts = session.execute(
                text("""
                    SELECT status, COUNT(*) 
                    FROM mapper_jobs 
                    GROUP BY status
                """)
            ).fetchall()
            
            print("\n" + "=" * 60)
            print("CCQ Mapper Database Statistics")
            print("=" * 60)
            print(f"Total Jobs: {job_count}")
            print(f"Mapping Results: {result_count}")
            print(f"Comparisons: {comparison_count}")
            print("\nJob Status Breakdown:")
            for status, count in status_counts:
                print(f"  {status}: {count}")
            print("=" * 60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='CCQ Mapper Database Initialization'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if tables and views exist'
    )
    
    parser.add_argument(
        '--init',
        action='store_true',
        help='Initialize tables (use SQL migration for production)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run database tests'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics'
    )
    
    args = parser.parse_args()
    
    if not any([args.check, args.init, args.test, args.stats]):
        parser.print_help()
        sys.exit(1)
    
    try:
        initializer = MapperDatabaseInitializer()
        
        if args.check:
            print("\n" + "=" * 60)
            print("Checking CCQ Mapper Database")
            print("=" * 60)
            
            table_status = initializer.check_tables()
            view_status = initializer.check_views()
            
            print("\nTable Status:")
            for name, exists in table_status.items():
                status = "✓ EXISTS" if exists else "✗ MISSING"
                print(f"  {name}: {status}")
            
            print("\nView Status:")
            for name, exists in view_status.items():
                status = "✓ EXISTS" if exists else "✗ MISSING"
                print(f"  {name}: {status}")
            
            all_tables = all(table_status.values())
            all_views = all(view_status.values())
            
            print("\n" + "=" * 60)
            if all_tables and all_views:
                print("✓ Database is fully set up")
            elif all_tables:
                print("⚠ Tables exist but views missing")
                print("  Run: psql -f database/migrations/add_mapper_tables.sql")
            else:
                print("✗ Database setup incomplete")
                print("  Run: psql -f database/migrations/add_mapper_tables.sql")
            print("=" * 60 + "\n")
        
        if args.init:
            print("\n" + "=" * 60)
            print("Initializing CCQ Mapper Tables")
            print("=" * 60)
            print("\nWARNING: For production, use SQL migration instead:")
            print("  psql -f database/migrations/add_mapper_tables.sql")
            print("\nProceeding with programmatic initialization...\n")
            
            initializer.initialize_tables()
            
            print("\n" + "=" * 60)
            print("Tables initialized")
            print("Next steps:")
            print("  1. Run add_mapper_tables.sql for views/functions")
            print("  2. Run --test to verify setup")
            print("=" * 60 + "\n")
        
        if args.test:
            print("\n" + "=" * 60)
            print("Running CCQ Mapper Database Tests")
            print("=" * 60 + "\n")
            
            initializer.run_tests()
        
        if args.stats:
            initializer.get_statistics()
    
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()