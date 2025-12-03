-- ============================================================================
-- FILE 1: database/migrations/schema.sql (UPDATED VERSION)
-- ============================================================================
-- CCQ Validator Database Schema
-- ================================
-- Complete database for CCQ's independent operation
-- Stores: validation metadata, job queue, search indexes
-- Does NOT store: actual financial data (only in JSON files)

-- ============================================================================
-- JOB QUEUE (CCQ's own queue, independent of Map Pro)
-- ============================================================================
CREATE TABLE validation_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Job identification
    filing_id VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    filing_type VARCHAR(50) NOT NULL,
    filing_date DATE NOT NULL,
    market VARCHAR(50) NOT NULL,
    
    -- File paths from Map Pro (metadata only)
    input_directory TEXT NOT NULL,
    
    -- Job status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    priority INTEGER DEFAULT 0,  -- Higher = more urgent
    
    -- Processing metadata
    assigned_worker VARCHAR(100),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    processing_time_seconds DECIMAL(10,2),
    
    -- Error tracking
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for job queue operations
CREATE INDEX idx_job_status ON validation_jobs(status);
CREATE INDEX idx_job_priority ON validation_jobs(priority DESC, created_at ASC);
CREATE INDEX idx_job_filing ON validation_jobs(filing_id);
CREATE INDEX idx_job_created ON validation_jobs(created_at);
CREATE INDEX idx_job_company ON validation_jobs(company_name);

-- Composite index for efficient job pickup
CREATE INDEX idx_pending_jobs ON validation_jobs(status, priority DESC, created_at ASC)
WHERE status = 'pending';

-- ============================================================================
-- VALIDATED FILINGS (Search index for completed validations)
-- ============================================================================
-- Registry of all validated filings for search and quick lookups
CREATE TABLE validated_filings (
    filing_id VARCHAR(255) PRIMARY KEY,
    
    -- Filing identification
    company_name VARCHAR(255) NOT NULL,
    cik VARCHAR(20),
    filing_type VARCHAR(50) NOT NULL,
    filing_date DATE NOT NULL,
    fiscal_year INTEGER,
    fiscal_period VARCHAR(10),  -- Q1, Q2, Q3, Q4, FY
    market VARCHAR(50) NOT NULL,
    
    -- Taxonomy information
    taxonomy_name VARCHAR(50),
    taxonomy_version VARCHAR(20),
    
    -- File paths (not actual data!)
    input_directory TEXT NOT NULL,
    output_directory TEXT NOT NULL,
    validation_report_path TEXT NOT NULL,
    
    -- Validation results summary
    validation_status VARCHAR(50) NOT NULL,  -- 'completed', 'partial_fail', 'failed'
    overall_pass BOOLEAN NOT NULL DEFAULT false,
    confidence_score DECIMAL(5,2),
    ready_for_analysis BOOLEAN NOT NULL DEFAULT false,  -- NEW: Indicates if data quality is sufficient
    
    -- Statement-level status
    income_statement_status VARCHAR(50),      -- 'passed', 'failed', 'warning'
    balance_sheet_status VARCHAR(50),
    cash_flow_status VARCHAR(50),
    other_statement_status VARCHAR(50),
    
    -- Null quality tracking
    null_quality_issues_count INTEGER DEFAULT 0,
    has_map_pro_nulls BOOLEAN DEFAULT false,  -- Nulls from Map Pro errors
    has_original_nulls BOOLEAN DEFAULT false, -- Nulls from source document
    
    -- Validation statistics
    total_checks_performed INTEGER,
    checks_passed INTEGER,
    checks_failed INTEGER,
    checks_warning INTEGER,
    vertical_checks_passed BOOLEAN,
    horizontal_checks_passed BOOLEAN,
    
    -- Anomaly summary
    critical_anomalies_count INTEGER DEFAULT 0,
    warning_anomalies_count INTEGER DEFAULT 0,
    info_anomalies_count INTEGER DEFAULT 0,
    
    -- Processing metadata
    processing_time_seconds DECIMAL(10,2),
    validated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Map Pro job reference (optional)
    map_pro_job_id VARCHAR(255)
);

-- Indexes for search functionality
CREATE INDEX idx_company_name ON validated_filings(company_name);
CREATE INDEX idx_company_filing_date ON validated_filings(company_name, filing_date DESC);
CREATE INDEX idx_filing_type ON validated_filings(filing_type);
CREATE INDEX idx_validation_status ON validated_filings(validation_status);
CREATE INDEX idx_fiscal_period ON validated_filings(fiscal_year, fiscal_period);
CREATE INDEX idx_confidence_score ON validated_filings(confidence_score);
CREATE INDEX idx_ready_for_analysis ON validated_filings(ready_for_analysis);  -- NEW INDEX
CREATE INDEX idx_overall_pass ON validated_filings(overall_pass);
CREATE INDEX idx_validated_at ON validated_filings(validated_at DESC);

-- Composite indexes for common queries
CREATE INDEX idx_company_year_period ON validated_filings(company_name, fiscal_year, fiscal_period);
CREATE INDEX idx_company_status ON validated_filings(company_name, validation_status);

-- Full-text search on company name (PostgreSQL specific)
CREATE INDEX idx_company_name_trgm ON validated_filings USING gin(company_name gin_trgm_ops);

-- ============================================================================
-- VALIDATION ANOMALIES (Optional - for detailed search)
-- ============================================================================
-- Stores individual anomalies for detailed querying
-- Note: Full details are in JSON files, this is for search only
CREATE TABLE validation_anomalies (
    anomaly_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filing_id VARCHAR(255) NOT NULL REFERENCES validated_filings(filing_id) ON DELETE CASCADE,
    
    -- Anomaly identification
    check_name VARCHAR(255) NOT NULL,
    check_category VARCHAR(100),  -- 'vertical', 'horizontal', 'qualitative', 'statistical'
    statement_type VARCHAR(50),   -- 'income_statement', 'balance_sheet', 'cash_flow', 'other'
    
    -- Anomaly details
    severity VARCHAR(50) NOT NULL,  -- 'critical', 'warning', 'info'
    description TEXT,
    concept_name VARCHAR(255),
    
    -- Values (for search/filtering, not primary data source)
    expected_value DECIMAL(20,4),
    actual_value DECIMAL(20,4),
    variance DECIMAL(20,4),
    variance_percentage DECIMAL(10,4),
    
    -- Timestamps
    detected_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_anomaly_filing ON validation_anomalies(filing_id);
CREATE INDEX idx_anomaly_severity ON validation_anomalies(severity);
CREATE INDEX idx_anomaly_check ON validation_anomalies(check_name);
CREATE INDEX idx_anomaly_statement ON validation_anomalies(statement_type);

-- ============================================================================
-- VALIDATION STATISTICS (Aggregated for dashboard/reporting)
-- ============================================================================
CREATE TABLE validation_statistics (
    stat_id SERIAL PRIMARY KEY,
    
    -- Time period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Aggregated counts
    total_validations INTEGER DEFAULT 0,
    successful_validations INTEGER DEFAULT 0,
    failed_validations INTEGER DEFAULT 0,
    partial_validations INTEGER DEFAULT 0,
    
    -- Average metrics
    avg_confidence_score DECIMAL(5,2),
    avg_processing_time DECIMAL(10,2),
    
    -- By market
    sec_validations INTEGER DEFAULT 0,
    fca_validations INTEGER DEFAULT 0,
    esma_validations INTEGER DEFAULT 0,
    
    -- Computed at
    computed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(period_start, period_end)
);

-- ============================================================================
-- SEARCH HELPER VIEWS
-- ============================================================================

-- Recent validations view
CREATE VIEW recent_validations AS
SELECT 
    filing_id,
    company_name,
    filing_type,
    filing_date,
    fiscal_year,
    fiscal_period,
    validation_status,
    overall_pass,
    confidence_score,
    ready_for_analysis,
    validated_at
FROM validated_filings
ORDER BY validated_at DESC
LIMIT 100;

-- Failed validations view
CREATE VIEW failed_validations AS
SELECT 
    filing_id,
    company_name,
    filing_type,
    filing_date,
    validation_status,
    confidence_score,
    critical_anomalies_count,
    validated_at,
    validation_report_path
FROM validated_filings
WHERE overall_pass = false
ORDER BY validated_at DESC;

-- Ready for analysis view (NEW)
CREATE VIEW ready_for_analysis AS
SELECT 
    filing_id,
    company_name,
    filing_type,
    filing_date,
    fiscal_year,
    fiscal_period,
    confidence_score,
    validation_report_path,
    output_directory
FROM validated_filings
WHERE ready_for_analysis = true
ORDER BY validated_at DESC;

-- Company summary view (for "show me all Apple filings")
CREATE VIEW company_validation_summary AS
SELECT 
    company_name,
    COUNT(*) as total_filings,
    COUNT(*) FILTER (WHERE overall_pass = true) as passed_filings,
    COUNT(*) FILTER (WHERE overall_pass = false) as failed_filings,
    COUNT(*) FILTER (WHERE ready_for_analysis = true) as ready_filings,
    AVG(confidence_score) as avg_confidence_score,
    MAX(validated_at) as last_validated,
    MIN(fiscal_year) as earliest_year,
    MAX(fiscal_year) as latest_year
FROM validated_filings
GROUP BY company_name
ORDER BY company_name;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to check if filing already validated
CREATE OR REPLACE FUNCTION is_filing_validated(p_filing_id VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM validated_filings 
        WHERE filing_id = p_filing_id 
        AND validation_status = 'completed'
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get company filings
CREATE OR REPLACE FUNCTION get_company_filings(
    p_company_name VARCHAR,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    filing_id VARCHAR,
    filing_type VARCHAR,
    filing_date DATE,
    fiscal_year INTEGER,
    fiscal_period VARCHAR,
    confidence_score DECIMAL,
    overall_pass BOOLEAN,
    ready_for_analysis BOOLEAN,
    validation_report_path TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        vf.filing_id,
        vf.filing_type,
        vf.filing_date,
        vf.fiscal_year,
        vf.fiscal_period,
        vf.confidence_score,
        vf.overall_pass,
        vf.ready_for_analysis,
        vf.validation_report_path
    FROM validated_filings vf
    WHERE vf.company_name = p_company_name
    ORDER BY vf.filing_date DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_validated_filings_updated_at
    BEFORE UPDATE ON validated_filings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE validated_filings IS 'Registry of validated filings for search and quick lookups. Actual validation data is in JSON files.';
COMMENT ON TABLE validation_anomalies IS 'Individual anomalies for search/filtering. Full details in JSON files.';
COMMENT ON TABLE validation_statistics IS 'Aggregated statistics for dashboard and reporting.';

COMMENT ON COLUMN validated_filings.filing_id IS 'Unique filing identifier from Map Pro';
COMMENT ON COLUMN validated_filings.output_directory IS 'Path to directory containing normalized statements and validation report';
COMMENT ON COLUMN validated_filings.validation_report_path IS 'Path to validation_report.json file';
COMMENT ON COLUMN validated_filings.ready_for_analysis IS 'True if confidence score meets threshold for downstream analysis (typically >= 70)';
COMMENT ON COLUMN validated_filings.has_map_pro_nulls IS 'True if null_quality.json indicates nulls from Map Pro errors';
COMMENT ON COLUMN validated_filings.has_original_nulls IS 'True if null_quality.json indicates nulls from original document';
COMMENT ON COLUMN validated_filings.vertical_checks_passed IS 'True if all intra-statement checks passed';
COMMENT ON COLUMN validated_filings.horizontal_checks_passed IS 'True if all inter-statement checks passed';

