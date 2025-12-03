"""
CCQ Validator Database Models

SQLAlchemy models for CCQ's independent operation.
Includes job queue and validation metadata.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Integer, String, Text, UUID
)
from sqlalchemy.types import DECIMAL as SQLDecimal  # Fix import
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ValidationJob(Base):
    """
    CCQ's own job queue for validation tasks.
    
    Independent of Map Pro - CCQ manages its own processing queue.
    Jobs can be created manually, via API, or by scanning for new filings.
    """
    __tablename__ = 'validation_jobs'
    
    # Primary key
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Job identification
    filing_id = Column(String(255), nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    filing_type = Column(String(50), nullable=False)
    filing_date = Column(Date, nullable=False)
    market = Column(String(50), nullable=False)
    
    # File paths from Map Pro (metadata only)
    input_directory = Column(Text, nullable=False)
    
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
    
    def __repr__(self):
        return (
            f"<ValidationJob(job_id={self.job_id}, filing_id={self.filing_id}, "
            f"status={self.status})>"
        )
    
    @property
    def is_pending(self) -> bool:
        """Check if job is pending."""
        return self.status == 'pending'
    
    @property
    def is_processing(self) -> bool:
        """Check if job is currently processing."""
        return self.status == 'processing'
    
    @property
    def is_completed(self) -> bool:
        """Check if job completed successfully."""
        return self.status == 'completed'
    
    @property
    def is_failed(self) -> bool:
        """Check if job failed."""
        return self.status == 'failed'
    
    @property
    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return self.retry_count < self.max_retries


class ValidatedFiling(Base):
    """
    Registry of validated filings for search and quick lookups.
    
    Stores summary information and file paths only.
    Actual validation data is in JSON files.
    """
    __tablename__ = 'validated_filings'
    
    # Primary identification
    filing_id = Column(String(255), primary_key=True)
    
    # Filing identification
    company_name = Column(String(255), nullable=False, index=True)
    cik = Column(String(20))
    filing_type = Column(String(50), nullable=False, index=True)
    filing_date = Column(Date, nullable=False)
    fiscal_year = Column(Integer, index=True)
    fiscal_period = Column(String(10))  # Q1, Q2, Q3, Q4, FY
    market = Column(String(50), nullable=False)
    
    # Taxonomy information
    taxonomy_name = Column(String(50))
    taxonomy_version = Column(String(20))
    
    # File paths (not actual data!)
    input_directory = Column(Text, nullable=False)
    output_directory = Column(Text, nullable=False)
    validation_report_path = Column(Text, nullable=False)
    
    # Validation results summary
    validation_status = Column(String(50), nullable=False, index=True)
    overall_pass = Column(Boolean, nullable=False, default=False, index=True)
    confidence_score = Column(SQLDecimal(5, 2), index=True)
    ready_for_analysis = Column(Boolean, nullable=False, default=False, index=True)

    # Statement-level status
    income_statement_status = Column(String(50))
    balance_sheet_status = Column(String(50))
    cash_flow_status = Column(String(50))
    other_statement_status = Column(String(50))
    
    # Null quality tracking
    null_quality_issues_count = Column(Integer, default=0)
    has_map_pro_nulls = Column(Boolean, default=False)
    has_original_nulls = Column(Boolean, default=False)
    
    # Validation statistics
    total_checks_performed = Column(Integer)
    checks_passed = Column(Integer)
    checks_failed = Column(Integer)
    checks_warning = Column(Integer)
    vertical_checks_passed = Column(Boolean)
    horizontal_checks_passed = Column(Boolean)
    
    # Anomaly summary
    critical_anomalies_count = Column(Integer, default=0)
    warning_anomalies_count = Column(Integer, default=0)
    info_anomalies_count = Column(Integer, default=0)
    
    # Processing metadata
    processing_time_seconds = Column(SQLDecimal(10, 2))
    validated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Map Pro job reference (optional)
    map_pro_job_id = Column(String(255))
    
    # Relationships
    anomalies = relationship("ValidationAnomaly", back_populates="filing", cascade="all, delete-orphan")
    
    def __repr__(self):
        return (
            f"<ValidatedFiling(filing_id={self.filing_id}, "
            f"company={self.company_name}, status={self.validation_status})>"
        )
    
    @property
    def passed(self) -> bool:
        """Check if validation passed."""
        return self.overall_pass
    
    @property
    def failed(self) -> bool:
        """Check if validation failed."""
        return not self.overall_pass
    
    @property
    def has_critical_anomalies(self) -> bool:
        """Check if there are critical anomalies."""
        return self.critical_anomalies_count > 0
    
    @property
    def statement_failures(self) -> list[str]:
        """Get list of failed statement types."""
        failures = []
        if self.income_statement_status == 'failed':
            failures.append('income_statement')
        if self.balance_sheet_status == 'failed':
            failures.append('balance_sheet')
        if self.cash_flow_status == 'failed':
            failures.append('cash_flow')
        if self.other_statement_status == 'failed':
            failures.append('other')
        return failures


class ValidationAnomaly(Base):
    """
    Individual validation anomalies for search/filtering.
    
    Stores summary of anomalies - full details in JSON files.
    """
    __tablename__ = 'validation_anomalies'
    
    # Primary key
    anomaly_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    filing_id = Column(String(255), ForeignKey('validated_filings.filing_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Anomaly identification
    check_name = Column(String(255), nullable=False, index=True)
    check_category = Column(String(100))  # vertical, horizontal, qualitative, statistical
    statement_type = Column(String(50), index=True)  # income_statement, balance_sheet, etc.
    
    # Anomaly details
    severity = Column(String(50), nullable=False, index=True)  # critical, warning, info
    description = Column(Text)
    concept_name = Column(String(255))
    
    # Values (for search/filtering, not primary data source)
    expected_value = Column(SQLDecimal(20, 4))
    actual_value = Column(SQLDecimal(20, 4))
    variance = Column(SQLDecimal(20, 4))
    variance_percentage = Column(SQLDecimal(10, 4))
    
    # Timestamp
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    filing = relationship("ValidatedFiling", back_populates="anomalies")
    
    def __repr__(self):
        return (
            f"<ValidationAnomaly(check={self.check_name}, "
            f"severity={self.severity}, filing={self.filing_id})>"
        )
    
    @property
    def is_critical(self) -> bool:
        """Check if anomaly is critical."""
        return self.severity == 'critical'
    
    @property
    def is_warning(self) -> bool:
        """Check if anomaly is warning level."""
        return self.severity == 'warning'


class ValidationStatistics(Base):
    """
    Aggregated validation statistics for dashboard/reporting.
    """
    __tablename__ = 'validation_statistics'
    
    # Primary key
    stat_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Time period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Aggregated counts
    total_validations = Column(Integer, default=0)
    successful_validations = Column(Integer, default=0)
    failed_validations = Column(Integer, default=0)
    partial_validations = Column(Integer, default=0)
    
    # Average metrics
    avg_confidence_score = Column(SQLDecimal(5, 2))
    avg_processing_time = Column(SQLDecimal(10, 2))
    
    # By market
    sec_validations = Column(Integer, default=0)
    fca_validations = Column(Integer, default=0)
    esma_validations = Column(Integer, default=0)
    
    # Computed at
    computed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return (
            f"<ValidationStatistics(period={self.period_start} to {self.period_end}, "
            f"total={self.total_validations})>"
        )


# Helper functions for job queue management

def create_validation_job(
    session,
    filing_id: str,
    company_name: str,
    filing_type: str,
    filing_date,
    market: str,
    input_directory: str,
    priority: int = 0
) -> ValidationJob:
    """
    Create a new validation job.
    
    Args:
        session: SQLAlchemy session
        filing_id: Unique filing identifier
        company_name: Company name
        filing_type: Filing type (10-K, 10-Q, etc.)
        filing_date: Filing date
        market: Market identifier (sec, fca, esma)
        input_directory: Path to input files from Map Pro
        priority: Job priority (higher = more urgent)
        
    Returns:
        Created ValidationJob object
    """
    job = ValidationJob(
        filing_id=filing_id,
        company_name=company_name,
        filing_type=filing_type,
        filing_date=filing_date,
        market=market,
        input_directory=input_directory,
        priority=priority,
        status='pending'
    )
    session.add(job)
    session.commit()
    return job


def get_pending_jobs(session, limit: int = 10) -> list[ValidationJob]:
    """
    Get pending validation jobs ordered by priority.
    
    Args:
        session: SQLAlchemy session
        limit: Maximum number of jobs to retrieve
        
    Returns:
        List of pending ValidationJob objects
    """
    return (
        session.query(ValidationJob)
        .filter(ValidationJob.status == 'pending')
        .order_by(
            ValidationJob.priority.desc(),
            ValidationJob.created_at.asc()
        )
        .limit(limit)
        .all()
    )


def update_job_status(
    session,
    job_id,
    status: str,
    error: Optional[str] = None
) -> None:
    """
    Update job status.
    
    Args:
        session: SQLAlchemy session
        job_id: Job UUID
        status: New status (processing, completed, failed)
        error: Error message if failed
    """
    job = session.query(ValidationJob).filter(ValidationJob.job_id == job_id).first()
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
        
        if error:
            job.last_error = error
            job.retry_count += 1
        
        session.commit()


def retry_failed_job(session, job_id) -> bool:
    """
    Retry a failed job if retries available.
    
    Args:
        session: SQLAlchemy session
        job_id: Job UUID
        
    Returns:
        True if job was reset to pending, False if max retries reached
    """
    job = session.query(ValidationJob).filter(ValidationJob.job_id == job_id).first()
    if job and job.can_retry:
        job.status = 'pending'
        job.assigned_worker = None
        job.updated_at = datetime.utcnow()
        session.commit()
        return True
    return False


# Helper functions for validated filings (search)

def get_company_filings(session, company_name: str, limit: int = 50) -> list[ValidatedFiling]:
    """
    Get all validated filings for a company.
    
    Args:
        session: SQLAlchemy session
        company_name: Company name to search
        limit: Maximum number of results
        
    Returns:
        List of ValidatedFiling objects
    """
    return (
        session.query(ValidatedFiling)
        .filter(ValidatedFiling.company_name == company_name)
        .order_by(ValidatedFiling.filing_date.desc())
        .limit(limit)
        .all()
    )


def is_filing_validated(session, filing_id: str) -> bool:
    """
    Check if a filing has been validated.
    
    Args:
        session: SQLAlchemy session
        filing_id: Filing ID to check
        
    Returns:
        True if filing exists and is completed
    """
    return (
        session.query(ValidatedFiling)
        .filter(
            ValidatedFiling.filing_id == filing_id,
            ValidatedFiling.validation_status == 'completed'
        )
        .first()
    ) is not None


def get_failed_filings(session, limit: int = 50) -> list[ValidatedFiling]:
    """
    Get recent failed validations.
    
    Args:
        session: SQLAlchemy session
        limit: Maximum number of results
        
    Returns:
        List of failed ValidatedFiling objects
    """
    return (
        session.query(ValidatedFiling)
        .filter(ValidatedFiling.overall_pass == False)
        .order_by(ValidatedFiling.validated_at.desc())
        .limit(limit)
        .all()
    )


def search_filings(
    session,
    company_name: Optional[str] = None,
    filing_type: Optional[str] = None,
    fiscal_year: Optional[int] = None,
    market: Optional[str] = None,
    overall_pass: Optional[bool] = None,
    limit: int = 100
) -> list[ValidatedFiling]:
    """
    Search validated filings with multiple criteria.
    
    Args:
        session: SQLAlchemy session
        company_name: Filter by company name (partial match)
        filing_type: Filter by filing type
        fiscal_year: Filter by fiscal year
        market: Filter by market
        overall_pass: Filter by pass/fail status
        limit: Maximum number of results
        
    Returns:
        List of matching ValidatedFiling objects
    """
    query = session.query(ValidatedFiling)
    
    if company_name:
        query = query.filter(ValidatedFiling.company_name.ilike(f'%{company_name}%'))
    if filing_type:
        query = query.filter(ValidatedFiling.filing_type == filing_type)
    if fiscal_year:
        query = query.filter(ValidatedFiling.fiscal_year == fiscal_year)
    if market:
        query = query.filter(ValidatedFiling.market == market)
    if overall_pass is not None:
        query = query.filter(ValidatedFiling.overall_pass == overall_pass)
    
    return query.order_by(ValidatedFiling.validated_at.desc()).limit(limit).all()