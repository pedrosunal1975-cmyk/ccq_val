"""
CCQ Mapper Database Models
===========================

SQLAlchemy models for CCQ Mapper's metadata tracking.

CRITICAL: These models store METADATA ONLY:
- File paths to inputs/outputs
- Mapping statistics
- Comparison results with Map Pro
- NO actual financial data

Actual financial data is ALWAYS in JSON files on disk.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Integer, String, Text, UUID, JSON
)
from sqlalchemy.types import DECIMAL as SQLDecimal
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from database.models.ccq_models import Base


class MapperJob(Base):
    """
    CCQ Mapper job queue for property-based classification mapping.
    
    Independent job queue for CCQ Mapper tasks.
    Runs BEFORE CCQ validation - produces mapped statements that can be validated.
    """
    __tablename__ = 'mapper_jobs'
    
    # Primary key
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Job identification
    filing_id = Column(String(255), nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    filing_type = Column(String(50), nullable=False)
    filing_date = Column(Date, nullable=False)
    market = Column(String(50), nullable=False)
    
    # Input file paths (READ-ONLY)
    xbrl_path = Column(Text, nullable=False)  # Raw XBRL filing
    parsed_facts_path = Column(Text, nullable=False)  # Parsed facts JSON
    taxonomy_paths = Column(JSON)  # List of taxonomy paths
    
    # Output path (WRITE)
    output_directory = Column(Text)  # Where CCQ mapped output goes
    
    # Job status
    status = Column(String(50), nullable=False, default='pending', index=True)
    priority = Column(Integer, default=0, index=True)
    
    # Processing metadata
    assigned_worker = Column(String(100))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    processing_time_seconds = Column(SQLDecimal(10, 2))
    
    # Error tracking
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to mapping result
    mapping_result = relationship("MappingResult", back_populates="job", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return (
            f"<MapperJob(job_id={self.job_id}, filing_id={self.filing_id}, "
            f"status={self.status})>"
        )
    
    @property
    def is_pending(self) -> bool:
        return self.status == 'pending'
    
    @property
    def is_processing(self) -> bool:
        return self.status == 'processing'
    
    @property
    def is_completed(self) -> bool:
        return self.status == 'completed'
    
    @property
    def is_failed(self) -> bool:
        return self.status == 'failed'
    
    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries


class MappingResult(Base):
    """
    Registry of completed CCQ Mapper results.
    
    Stores summary and file paths only - actual mapped statements are in JSON files.
    """
    __tablename__ = 'mapping_results'
    
    # Primary key
    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('mapper_jobs.job_id', ondelete='CASCADE'), nullable=False, unique=True)
    filing_id = Column(String(255), nullable=False, index=True)
    
    # Filing information
    company_name = Column(String(255), nullable=False, index=True)
    filing_type = Column(String(50), nullable=False)
    filing_date = Column(Date, nullable=False)
    market = Column(String(50), nullable=False)
    
    # Output paths (METADATA - actual data in files)
    output_directory = Column(Text, nullable=False)
    balance_sheet_path = Column(Text)
    income_statement_path = Column(Text)
    cash_flow_path = Column(Text)
    other_statement_path = Column(Text)
    
    # Mapping statistics
    total_facts_processed = Column(Integer, default=0)
    facts_classified = Column(Integer, default=0)
    clusters_formed = Column(Integer, default=0)
    statements_constructed = Column(Integer, default=0)
    
    # Statement-level success
    balance_sheet_constructed = Column(Boolean, default=False)
    income_statement_constructed = Column(Boolean, default=False)
    cash_flow_constructed = Column(Boolean, default=False)
    other_constructed = Column(Boolean, default=False)
    
    # Classification statistics (property-based)
    monetary_currency_count = Column(Integer, default=0)
    monetary_shares_count = Column(Integer, default=0)
    temporal_instant_count = Column(Integer, default=0)
    temporal_duration_count = Column(Integer, default=0)
    accounting_debit_count = Column(Integer, default=0)
    accounting_credit_count = Column(Integer, default=0)
    
    # Validation against taxonomy (post-construction)
    taxonomy_validation_pass_rate = Column(SQLDecimal(5, 2))
    taxonomy_mismatches_count = Column(Integer, default=0)
    
    # Success metrics
    mapping_success = Column(Boolean, nullable=False, default=False)
    confidence_score = Column(SQLDecimal(5, 2))  # Overall confidence
    
    # Processing metadata
    processing_time_seconds = Column(SQLDecimal(10, 2))
    mapped_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    job = relationship("MapperJob", back_populates="mapping_result")
    comparison = relationship("MapProComparison", back_populates="mapping_result", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return (
            f"<MappingResult(filing_id={self.filing_id}, "
            f"company={self.company_name}, success={self.mapping_success})>"
        )
    
    @property
    def statements_found(self) -> list[str]:
        """Get list of successfully constructed statement types."""
        statements = []
        if self.balance_sheet_constructed:
            statements.append('balance_sheet')
        if self.income_statement_constructed:
            statements.append('income_statement')
        if self.cash_flow_constructed:
            statements.append('cash_flow')
        if self.other_constructed:
            statements.append('other')
        return statements
    
    @property
    def classification_summary(self) -> dict:
        """Get summary of classification results."""
        return {
            'monetary': {
                'currency': self.monetary_currency_count,
                'shares': self.monetary_shares_count
            },
            'temporal': {
                'instant': self.temporal_instant_count,
                'duration': self.temporal_duration_count
            },
            'accounting': {
                'debit': self.accounting_debit_count,
                'credit': self.accounting_credit_count
            }
        }


class MapProComparison(Base):
    """
    Comparison results between CCQ Mapper and Map Pro.
    
    This is the VALIDATION - independent agreement between two systems.
    """
    __tablename__ = 'map_pro_comparisons'
    
    # Primary key
    comparison_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    result_id = Column(UUID(as_uuid=True), ForeignKey('mapping_results.result_id', ondelete='CASCADE'), nullable=False, unique=True)
    filing_id = Column(String(255), nullable=False, index=True)
    
    # Comparison metadata
    map_pro_output_path = Column(Text)  # Path to Map Pro's mapped statements
    comparison_performed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Overall agreement
    overall_agreement = Column(Boolean, default=False, index=True)
    agreement_rate = Column(SQLDecimal(5, 2), index=True)  # Percentage
    
    # Concept-level comparison
    total_concepts_compared = Column(Integer, default=0)
    concepts_agreed = Column(Integer, default=0)
    concepts_disagreed = Column(Integer, default=0)
    
    # Statement-level agreement
    balance_sheet_agreement = Column(SQLDecimal(5, 2))
    income_statement_agreement = Column(SQLDecimal(5, 2))
    cash_flow_agreement = Column(SQLDecimal(5, 2))
    
    # Value differences
    value_differences_count = Column(Integer, default=0)
    max_value_difference = Column(SQLDecimal(20, 4))
    avg_value_difference = Column(SQLDecimal(20, 4))
    
    # Classification differences
    classification_differences_count = Column(Integer, default=0)
    statement_assignment_differences = Column(Integer, default=0)
    
    # Detailed comparison report path
    comparison_report_path = Column(Text)  # Path to detailed JSON report
    
    # Relationships
    mapping_result = relationship("MappingResult", back_populates="comparison")
    
    def __repr__(self):
        return (
            f"<MapProComparison(filing_id={self.filing_id}, "
            f"agreement_rate={self.agreement_rate}%)>"
        )
    
    @property
    def has_high_agreement(self) -> bool:
        """Check if agreement rate is >= 90%."""
        return self.agreement_rate and self.agreement_rate >= 90.0
    
    @property
    def needs_investigation(self) -> bool:
        """Check if comparison shows significant disagreements."""
        return not self.overall_agreement or (self.concepts_disagreed > 10)


class MapperStatistics(Base):
    """
    Aggregated CCQ Mapper statistics for monitoring.
    """
    __tablename__ = 'mapper_statistics'
    
    # Primary key
    stat_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Time period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Job statistics
    total_jobs = Column(Integer, default=0)
    successful_mappings = Column(Integer, default=0)
    failed_mappings = Column(Integer, default=0)
    
    # Processing metrics
    avg_processing_time = Column(SQLDecimal(10, 2))
    avg_facts_per_filing = Column(SQLDecimal(10, 2))
    avg_clusters_per_filing = Column(SQLDecimal(10, 2))
    
    # Agreement with Map Pro
    avg_agreement_rate = Column(SQLDecimal(5, 2))
    high_agreement_count = Column(Integer, default=0)  # >= 90%
    low_agreement_count = Column(Integer, default=0)  # < 90%
    
    # Statement construction rates
    balance_sheet_success_rate = Column(SQLDecimal(5, 2))
    income_statement_success_rate = Column(SQLDecimal(5, 2))
    cash_flow_success_rate = Column(SQLDecimal(5, 2))
    
    # Computed at
    computed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return (
            f"<MapperStatistics(period={self.period_start} to {self.period_end}, "
            f"total_jobs={self.total_jobs})>"
        )


# ============================================================================
# HELPER FUNCTIONS - Mapper Job Queue
# ============================================================================

def create_mapper_job(
    session,
    filing_id: str,
    company_name: str,
    filing_type: str,
    filing_date,
    market: str,
    xbrl_path: str,
    parsed_facts_path: str,
    taxonomy_paths: list,
    priority: int = 0
) -> MapperJob:
    """
    Create a new CCQ Mapper job.
    
    Args:
        session: SQLAlchemy session
        filing_id: Unique filing identifier
        company_name: Company name
        filing_type: Filing type (10-K, 10-Q, etc.)
        filing_date: Filing date
        market: Market identifier (sec, fca, esma)
        xbrl_path: Path to raw XBRL filing
        parsed_facts_path: Path to parsed facts JSON
        taxonomy_paths: List of taxonomy file paths
        priority: Job priority (higher = more urgent)
        
    Returns:
        Created MapperJob object
    """
    job = MapperJob(
        filing_id=filing_id,
        company_name=company_name,
        filing_type=filing_type,
        filing_date=filing_date,
        market=market,
        xbrl_path=xbrl_path,
        parsed_facts_path=parsed_facts_path,
        taxonomy_paths=taxonomy_paths,
        priority=priority,
        status='pending'
    )
    session.add(job)
    session.commit()
    return job


def get_pending_mapper_jobs(session, limit: int = 10) -> list[MapperJob]:
    """
    Get pending mapper jobs ordered by priority.
    
    Args:
        session: SQLAlchemy session
        limit: Maximum number of jobs to retrieve
        
    Returns:
        List of pending MapperJob objects
    """
    return (
        session.query(MapperJob)
        .filter(MapperJob.status == 'pending')
        .order_by(
            MapperJob.priority.desc(),
            MapperJob.created_at.asc()
        )
        .limit(limit)
        .all()
    )


def update_mapper_job_status(
    session,
    job_id,
    status: str,
    output_directory: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """
    Update mapper job status.
    
    Args:
        session: SQLAlchemy session
        job_id: Job UUID
        status: New status (processing, completed, failed)
        output_directory: Path to output directory (if completed)
        error: Error message (if failed)
    """
    job = session.query(MapperJob).filter(MapperJob.job_id == job_id).first()
    if job:
        job.status = status
        job.updated_at = datetime.utcnow()
        
        if status == 'processing':
            job.started_at = datetime.utcnow()
        elif status in ('completed', 'failed'):
            job.completed_at = datetime.utcnow()
            if job.started_at:
                elapsed = (job.completed_at - job.started_at).total_seconds()
                job.processing_time_seconds = Decimal(str(elapsed))
        
        if output_directory:
            job.output_directory = output_directory
        
        if error:
            job.last_error = error
            job.retry_count += 1
        
        session.commit()


# ============================================================================
# HELPER FUNCTIONS - Mapping Results
# ============================================================================

def create_mapping_result(
    session,
    job_id,
    filing_id: str,
    company_name: str,
    filing_type: str,
    filing_date,
    market: str,
    output_directory: str,
    statistics: dict
) -> MappingResult:
    """
    Create mapping result record.
    
    Args:
        session: SQLAlchemy session
        job_id: Associated mapper job ID
        filing_id: Filing identifier
        company_name: Company name
        filing_type: Filing type
        filing_date: Filing date
        market: Market identifier
        output_directory: Output directory path
        statistics: Mapping statistics dictionary
        
    Returns:
        Created MappingResult object
    """
    result = MappingResult(
        job_id=job_id,
        filing_id=filing_id,
        company_name=company_name,
        filing_type=filing_type,
        filing_date=filing_date,
        market=market,
        output_directory=output_directory,
        total_facts_processed=statistics.get('total_facts', 0),
        facts_classified=statistics.get('classified_facts', 0),
        clusters_formed=statistics.get('clusters_formed', 0),
        statements_constructed=statistics.get('statements_constructed', 0),
        mapping_success=statistics.get('success', False),
        confidence_score=statistics.get('confidence_score'),
        processing_time_seconds=statistics.get('processing_time_seconds')
    )
    session.add(result)
    session.commit()
    return result


def get_mapping_result_by_filing(session, filing_id: str) -> Optional[MappingResult]:
    """
    Get mapping result for a filing.
    
    Args:
        session: SQLAlchemy session
        filing_id: Filing identifier
        
    Returns:
        MappingResult object or None
    """
    return (
        session.query(MappingResult)
        .filter(MappingResult.filing_id == filing_id)
        .order_by(MappingResult.mapped_at.desc())
        .first()
    )


# ============================================================================
# HELPER FUNCTIONS - Map Pro Comparison
# ============================================================================

def create_comparison_result(
    session,
    result_id,
    filing_id: str,
    comparison_data: dict
) -> MapProComparison:
    """
    Create Map Pro comparison record.
    
    Args:
        session: SQLAlchemy session
        result_id: Associated mapping result ID
        filing_id: Filing identifier
        comparison_data: Comparison results dictionary
        
    Returns:
        Created MapProComparison object
    """
    comparison = MapProComparison(
        result_id=result_id,
        filing_id=filing_id,
        map_pro_output_path=comparison_data.get('map_pro_path'),
        overall_agreement=comparison_data.get('overall_agreement', False),
        agreement_rate=comparison_data.get('agreement_rate'),
        total_concepts_compared=comparison_data.get('total_concepts', 0),
        concepts_agreed=comparison_data.get('concepts_agreed', 0),
        concepts_disagreed=comparison_data.get('concepts_disagreed', 0),
        value_differences_count=comparison_data.get('value_differences_count', 0),
        comparison_report_path=comparison_data.get('report_path')
    )
    session.add(comparison)
    session.commit()
    return comparison


def get_high_agreement_mappings(session, limit: int = 50) -> list[MapProComparison]:
    """
    Get mappings with high agreement (>= 90%) with Map Pro.
    
    Args:
        session: SQLAlchemy session
        limit: Maximum number of results
        
    Returns:
        List of MapProComparison objects
    """
    return (
        session.query(MapProComparison)
        .filter(MapProComparison.agreement_rate >= 90.0)
        .order_by(MapProComparison.comparison_performed_at.desc())
        .limit(limit)
        .all()
    )


def get_disagreements(session, threshold: float = 80.0, limit: int = 50) -> list[MapProComparison]:
    """
    Get mappings with low agreement that need investigation.
    
    Args:
        session: SQLAlchemy session
        threshold: Agreement rate threshold (%)
        limit: Maximum number of results
        
    Returns:
        List of MapProComparison objects
    """
    return (
        session.query(MapProComparison)
        .filter(MapProComparison.agreement_rate < threshold)
        .order_by(MapProComparison.agreement_rate.asc())
        .limit(limit)
        .all()
    )


__all__ = [
    'MapperJob',
    'MappingResult',
    'MapProComparison',
    'MapperStatistics',
    'create_mapper_job',
    'get_pending_mapper_jobs',
    'update_mapper_job_status',
    'create_mapping_result',
    'get_mapping_result_by_filing',
    'create_comparison_result',
    'get_high_agreement_mappings',
    'get_disagreements',
]