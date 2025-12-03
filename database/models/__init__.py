"""
CCQ Database Models

SQLAlchemy models for CCQ's independent operation.
Includes job queue and validation search indexes.
"""

from .ccq_models import (
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
    # Job queue
    'create_validation_job',
    'get_pending_jobs',
    'update_job_status',
    'retry_failed_job',
    # Search
    'get_company_filings',
    'is_filing_validated',
    'get_failed_filings',
    'search_filings',
]