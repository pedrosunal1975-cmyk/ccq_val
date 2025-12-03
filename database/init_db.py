"""
CCQ Validator Database Module

Provides database models, initialization, and helper functions.

Components:
- models: SQLAlchemy models for job queue and validation metadata
- init_db: Database initialization script
- schema.sql: Complete SQL schema definition
"""

from .models import (
    Base,
    ValidationJob,
    ValidatedFiling,
    ValidationAnomaly,
    ValidationStatistics,
    # Job queue functions
    create_validation_job,
    get_pending_jobs,
    update_job_status,
    retry_failed_job,
    # Search functions
    get_company_filings,
    is_filing_validated,
    get_failed_filings,
    search_filings,
)

__all__ = [
    'Base',
    'ValidationJob',
    'ValidatedFiling',
    'ValidationAnomaly',
    'ValidationStatistics',
    'create_validation_job',
    'get_pending_jobs',
    'update_job_status',
    'retry_failed_job',
    'get_company_filings',
    'is_filing_validated',
    'get_failed_filings',
    'search_filings',
]