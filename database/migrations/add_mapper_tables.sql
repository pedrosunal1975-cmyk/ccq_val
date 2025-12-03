-- ============================================================================
-- CCQ Mapper Database Migration
-- ============================================================================
-- Adds tables for CCQ Mapper's property-based classification system
-- Run this AFTER the main schema.sql
-- Date: 2025-11-16

-- ============================================================================
-- MAPPER JOB QUEUE
-- ============================================================================
CREATE TABLE IF NOT EXISTS mapper_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Job identification
    filing_id VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    filing_type VARCHAR(50) NOT NULL,
    filing_date DATE NOT NULL,
    market VARCHAR(50) NOT NULL,
    
    -- Input file paths (READ-ONLY metadata)
    xbrl_path TEXT NOT NULL,              -- Raw XBRL filing
    parsed_facts_path TEXT NOT NULL,      -- Parsed facts JSON
    taxonomy_paths JSONB,                 -- List of taxonomy paths
    
    -- Output path (WRITE)
    output_directory TEXT,                -- Where CCQ mapped output goes
    
    -- Job status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    
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

-- Indexes for mapper job queue
CREATE INDEX IF NOT EXISTS idx_mapper_job_status ON mapper_jobs(status);
CREATE INDEX IF NOT EXISTS idx_mapper_job_priority ON mapper_jobs(priority DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_mapper_job_filing ON mapper_jobs(filing_id);
CREATE INDEX IF NOT EXISTS idx_mapper_job_created ON mapper_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_mapper_job_company ON mapper_jobs(company_name);

-- Composite index for efficient job pickup
CREATE INDEX IF NOT EXISTS idx_mapper_pending_jobs ON mapper_jobs(status, priority DESC, created_at ASC)
WHERE status = 'pending';

-- ============================================================================
-- MAPPING RESULTS (CCQ Mapper Output Registry)
-- ============================================================================
CREATE TABLE IF NOT EXISTS mapping_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL UNIQUE REFERENCES mapper_jobs(job_id) ON DELETE CASCADE,
    filing_id VARCHAR(255) NOT NULL,
    
    -- Filing information
    company_name VARCHAR(255) NOT NULL,
    filing_type VARCHAR(50) NOT NULL,
    filing_date DATE NOT NULL,
    market VARCHAR(50) NOT NULL,
    
    -- Output paths (METADATA - actual data in files)
    output_directory TEXT NOT NULL,
    balance_sheet_path TEXT,
    income_statement_path TEXT,
    cash_flow_path TEXT,
    other_statement_path TEXT,
    
    -- Mapping statistics
    total_facts_processed INTEGER DEFAULT 0,
    facts_classified INTEGER DEFAULT 0,
    clusters_formed INTEGER DEFAULT 0,
    statements_constructed INTEGER DEFAULT 0,
    
    -- Statement-level success
    balance_sheet_constructed BOOLEAN DEFAULT false,
    income_statement_constructed BOOLEAN DEFAULT false,
    cash_flow_constructed BOOLEAN DEFAULT false,
    other_constructed BOOLEAN DEFAULT false,
    
    -- Classification statistics (property-based)
    monetary_currency_count INTEGER DEFAULT 0,
    monetary_shares_count INTEGER DEFAULT 0,
    temporal_instant_count INTEGER DEFAULT 0,
    temporal_duration_count INTEGER DEFAULT 0,
    accounting_debit_count INTEGER DEFAULT 0,
    accounting_credit_count INTEGER DEFAULT 0,
    
    -- Validation against taxonomy (post-construction)
    taxonomy_validation_pass_rate DECIMAL(5,2),
    taxonomy_mismatches_count INTEGER DEFAULT 0,
    
    -- Success metrics
    mapping_success BOOLEAN NOT NULL DEFAULT false,
    confidence_score DECIMAL(5,2),
    
    -- Processing metadata
    processing_time_seconds DECIMAL(10,2),
    mapped_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT idx_mapping_result_filing UNIQUE (filing_id)
);

-- Indexes for mapping results
CREATE INDEX IF NOT EXISTS idx_mapping_company ON mapping_results(company_name);
CREATE INDEX IF NOT EXISTS idx_mapping_filing_date ON mapping_results(filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_mapping_success ON mapping_results(mapping_success);
CREATE INDEX IF NOT EXISTS idx_mapping_mapped_at ON mapping_results(mapped_at DESC);
CREATE INDEX IF NOT EXISTS idx_mapping_filing_id ON mapping_results(filing_id);

-- ============================================================================
-- MAP PRO COMPARISONS (Independent Validation)
-- ============================================================================
CREATE TABLE IF NOT EXISTS map_pro_comparisons (
    comparison_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id UUID NOT NULL UNIQUE REFERENCES mapping_results(result_id) ON DELETE CASCADE,
    filing_id VARCHAR(255) NOT NULL,
    
    -- Comparison metadata
    map_pro_output_path TEXT,
    comparison_performed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Overall agreement
    overall_agreement BOOLEAN DEFAULT false,
    agreement_rate DECIMAL(5,2),
    
    -- Concept-level comparison
    total_concepts_compared INTEGER DEFAULT 0,
    concepts_agreed INTEGER DEFAULT 0,
    concepts_disagreed INTEGER DEFAULT 0,
    
    -- Statement-level agreement
    balance_sheet_agreement DECIMAL(5,2),
    income_statement_agreement DECIMAL(5,2),
    cash_flow_agreement DECIMAL(5,2),
    
    -- Value differences
    value_differences_count INTEGER DEFAULT 0,
    max_value_difference DECIMAL(20,4),
    avg_value_difference DECIMAL(20,4),
    
    -- Classification differences
    classification_differences_count INTEGER DEFAULT 0,
    statement_assignment_differences INTEGER DEFAULT 0,
    
    -- Detailed comparison report path
    comparison_report_path TEXT
);

-- Indexes for comparisons
CREATE INDEX IF NOT EXISTS idx_comparison_filing ON map_pro_comparisons(filing_id);
CREATE INDEX IF NOT EXISTS idx_comparison_agreement ON map_pro_comparisons(overall_agreement);
CREATE INDEX IF NOT EXISTS idx_comparison_rate ON map_pro_comparisons(agreement_rate);
CREATE INDEX IF NOT EXISTS idx_comparison_performed ON map_pro_comparisons(comparison_performed_at DESC);

-- ============================================================================
-- MAPPER STATISTICS (Aggregated Metrics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS mapper_statistics (
    stat_id SERIAL PRIMARY KEY,
    
    -- Time period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Job statistics
    total_jobs INTEGER DEFAULT 0,
    successful_mappings INTEGER DEFAULT 0,
    failed_mappings INTEGER DEFAULT 0,
    
    -- Processing metrics
    avg_processing_time DECIMAL(10,2),
    avg_facts_per_filing DECIMAL(10,2),
    avg_clusters_per_filing DECIMAL(10,2),
    
    -- Agreement with Map Pro
    avg_agreement_rate DECIMAL(5,2),
    high_agreement_count INTEGER DEFAULT 0,  -- >= 90%
    low_agreement_count INTEGER DEFAULT 0,   -- < 90%
    
    -- Statement construction rates
    balance_sheet_success_rate DECIMAL(5,2),
    income_statement_success_rate DECIMAL(5,2),
    cash_flow_success_rate DECIMAL(5,2),
    
    -- Computed at
    computed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(period_start, period_end)
);

-- ============================================================================
-- VIEWS FOR CCQ MAPPER
-- ============================================================================

-- Recent mapper jobs view
CREATE OR REPLACE VIEW recent_mapper_jobs AS
SELECT 
    job_id,
    filing_id,
    company_name,
    filing_type,
    filing_date,
    status,
    processing_time_seconds,
    created_at,
    completed_at
FROM mapper_jobs
ORDER BY created_at DESC
LIMIT 100;

-- Successful mappings with high agreement
CREATE OR REPLACE VIEW validated_mappings AS
SELECT 
    mr.filing_id,
    mr.company_name,
    mr.filing_type,
    mr.filing_date,
    mr.mapping_success,
    mr.confidence_score,
    mpc.agreement_rate,
    mpc.overall_agreement,
    mr.output_directory,
    mpc.comparison_report_path
FROM mapping_results mr
LEFT JOIN map_pro_comparisons mpc ON mr.result_id = mpc.result_id
WHERE mr.mapping_success = true
ORDER BY mr.mapped_at DESC;

-- Disagreements requiring investigation
CREATE OR REPLACE VIEW mapper_disagreements AS
SELECT 
    mr.filing_id,
    mr.company_name,
    mr.filing_type,
    mpc.agreement_rate,
    mpc.concepts_disagreed,
    mpc.value_differences_count,
    mpc.comparison_report_path,
    mr.output_directory,
    mpc.comparison_performed_at
FROM mapping_results mr
INNER JOIN map_pro_comparisons mpc ON mr.result_id = mpc.result_id
WHERE mpc.overall_agreement = false OR mpc.agreement_rate < 90.0
ORDER BY mpc.agreement_rate ASC, mpc.comparison_performed_at DESC;

-- Mapper performance summary
CREATE OR REPLACE VIEW mapper_performance AS
SELECT 
    company_name,
    COUNT(*) as total_mappings,
    COUNT(*) FILTER (WHERE mapping_success = true) as successful_mappings,
    AVG(confidence_score) as avg_confidence,
    AVG(processing_time_seconds) as avg_processing_time,
    AVG(total_facts_processed) as avg_facts_processed
FROM mapping_results
GROUP BY company_name
ORDER BY total_mappings DESC;

-- ============================================================================
-- FUNCTIONS FOR CCQ MAPPER
-- ============================================================================

-- Function to check if filing already mapped
CREATE OR REPLACE FUNCTION is_filing_mapped(p_filing_id VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM mapping_results 
        WHERE filing_id = p_filing_id 
        AND mapping_success = true
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get mapper job by filing
CREATE OR REPLACE FUNCTION get_mapper_job_by_filing(p_filing_id VARCHAR)
RETURNS TABLE (
    job_id UUID,
    status VARCHAR,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    processing_time_seconds DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mj.job_id,
        mj.status,
        mj.created_at,
        mj.completed_at,
        mj.processing_time_seconds
    FROM mapper_jobs mj
    WHERE mj.filing_id = p_filing_id
    ORDER BY mj.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to get comparison results for company
CREATE OR REPLACE FUNCTION get_company_comparisons(
    p_company_name VARCHAR,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    filing_id VARCHAR,
    filing_date DATE,
    agreement_rate DECIMAL,
    overall_agreement BOOLEAN,
    concepts_agreed INTEGER,
    concepts_disagreed INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mr.filing_id,
        mr.filing_date,
        mpc.agreement_rate,
        mpc.overall_agreement,
        mpc.concepts_agreed,
        mpc.concepts_disagreed
    FROM mapping_results mr
    INNER JOIN map_pro_comparisons mpc ON mr.result_id = mpc.result_id
    WHERE mr.company_name = p_company_name
    ORDER BY mr.filing_date DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at for mapper_jobs
CREATE TRIGGER update_mapper_jobs_updated_at
    BEFORE UPDATE ON mapper_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE mapper_jobs IS 'CCQ Mapper job queue - property-based classification mapping tasks';
COMMENT ON TABLE mapping_results IS 'Registry of CCQ Mapper results. Actual mapped statements are in JSON files.';
COMMENT ON TABLE map_pro_comparisons IS 'Comparison between CCQ Mapper and Map Pro for independent validation';
COMMENT ON TABLE mapper_statistics IS 'Aggregated mapper performance metrics';

COMMENT ON COLUMN mapper_jobs.xbrl_path IS 'Path to raw XBRL filing (read-only input)';
COMMENT ON COLUMN mapper_jobs.parsed_facts_path IS 'Path to parsed facts JSON (read-only input)';
COMMENT ON COLUMN mapper_jobs.taxonomy_paths IS 'JSON array of taxonomy file paths (for validation only)';
COMMENT ON COLUMN mapper_jobs.output_directory IS 'Path where CCQ mapped statements are written';

COMMENT ON COLUMN mapping_results.output_directory IS 'Directory containing CCQ mapped statements (JSON files)';
COMMENT ON COLUMN mapping_results.taxonomy_validation_pass_rate IS 'Percentage of facts that matched taxonomy expectations (post-construction validation)';

COMMENT ON COLUMN map_pro_comparisons.overall_agreement IS 'True if agreement rate >= 90% (high confidence in both systems)';
COMMENT ON COLUMN map_pro_comparisons.agreement_rate IS 'Percentage of concepts where CCQ and Map Pro agreed';
COMMENT ON COLUMN map_pro_comparisons.comparison_report_path IS 'Path to detailed JSON comparison report';

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '======================================================';
    RAISE NOTICE 'CCQ Mapper Tables Created Successfully';
    RAISE NOTICE '======================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - mapper_jobs (job queue)';
    RAISE NOTICE '  - mapping_results (output registry)';
    RAISE NOTICE '  - map_pro_comparisons (validation)';
    RAISE NOTICE '  - mapper_statistics (metrics)';
    RAISE NOTICE '';
    RAISE NOTICE 'Views created:';
    RAISE NOTICE '  - recent_mapper_jobs';
    RAISE NOTICE '  - validated_mappings';
    RAISE NOTICE '  - mapper_disagreements';
    RAISE NOTICE '  - mapper_performance';
    RAISE NOTICE '';
    RAISE NOTICE 'Ready to run CCQ Mapper!';
    RAISE NOTICE '======================================================';
END $$;