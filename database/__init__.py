"""
CCQ Database Module
===================

Database models, initialization, and helper functions for both
CCQ Validator and CCQ Mapper.

Components:
- CCQ Validator models (validation jobs, validated filings)
- CCQ Mapper models (mapper jobs, mapping results, comparisons)
- Database initialization and migrations
- Helper functions for job queue and search operations
"""

# CCQ Validator models and functions
from .models.ccq_models import (
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

# CCQ Mapper models and functions
from .models.mapper_models import (
    MapperJob,
    MappingResult,
    MapProComparison,
    MapperStatistics,
    # Mapper job queue functions
    create_mapper_job,
    get_pending_mapper_jobs,
    update_mapper_job_status,
    # Mapping result functions
    create_mapping_result,
    get_mapping_result_by_filing,
    # Comparison functions
    create_comparison_result,
    get_high_agreement_mappings,
    get_disagreements,
)

__all__ = [
    # Base
    'Base',
    
    # CCQ Validator Models
    'ValidationJob',
    'ValidatedFiling',
    'ValidationAnomaly',
    'ValidationStatistics',
    
    # CCQ Mapper Models
    'MapperJob',
    'MappingResult',
    'MapProComparison',
    'MapperStatistics',
    
    # Validator Job Queue
    'create_validation_job',
    'get_pending_jobs',
    'update_job_status',
    'retry_failed_job',
    
    # Validator Search
    'get_company_filings',
    'is_filing_validated',
    'get_failed_filings',
    'search_filings',
    
    # Mapper Job Queue
    'create_mapper_job',
    'get_pending_mapper_jobs',
    'update_mapper_job_status',
    
    # Mapper Results
    'create_mapping_result',
    'get_mapping_result_by_filing',
    
    # Mapper Comparisons
    'create_comparison_result',
    'get_high_agreement_mappings',
    'get_disagreements',
]