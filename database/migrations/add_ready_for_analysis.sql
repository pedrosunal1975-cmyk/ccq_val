-- ============================================================================
-- FILE 2: database/migrations/add_ready_for_analysis.sql
-- ============================================================================
-- Migration: Add ready_for_analysis column
-- Purpose: For existing databases that need to be updated
-- Date: 2025-11-14

-- Add the column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'validated_filings' 
        AND column_name = 'ready_for_analysis'
    ) THEN
        ALTER TABLE validated_filings 
        ADD COLUMN ready_for_analysis BOOLEAN NOT NULL DEFAULT FALSE;
        
        RAISE NOTICE 'Column ready_for_analysis added to validated_filings';
    ELSE
        RAISE NOTICE 'Column ready_for_analysis already exists';
    END IF;
END $$;

-- Create index if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'validated_filings' 
        AND indexname = 'idx_ready_for_analysis'
    ) THEN
        CREATE INDEX idx_ready_for_analysis ON validated_filings(ready_for_analysis);
        RAISE NOTICE 'Index idx_ready_for_analysis created';
    ELSE
        RAISE NOTICE 'Index idx_ready_for_analysis already exists';
    END IF;
END $$;

-- Update existing records: set ready_for_analysis based on confidence_score
-- Typically, scores >= 70 are considered ready for analysis
UPDATE validated_filings 
SET ready_for_analysis = (confidence_score >= 70.0)
WHERE ready_for_analysis = FALSE;

RAISE NOTICE 'Updated existing records with ready_for_analysis values';


-- ============================================================================
-- FILE 3: database/reset_database.sh (BASH SCRIPT)
-- ============================================================================
#!/bin/bash
# Database Reset Script for CCQ Validator
# Drops and recreates the ccq_validator database with fresh schema

set -e  # Exit on error

DB_NAME="ccq_validator"
DB_USER="map_pro_user"
DB_HOST="localhost"
DB_PORT="5432"

echo "=========================================="
echo "CCQ Validator Database Reset"
echo "=========================================="
echo ""
echo "WARNING: This will DROP the database '$DB_NAME' and recreate it!"
echo "All existing data will be lost."
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Operation cancelled."
    exit 0
fi

echo ""
echo "Step 1: Dropping existing database..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
echo "✓ Database dropped"

echo ""
echo "Step 2: Creating new database..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d postgres -c "CREATE DATABASE $DB_NAME;"
echo "✓ Database created"

echo ""
echo "Step 3: Enabling required extensions..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
echo "✓ Extensions enabled"

echo ""
echo "Step 4: Running schema..."
psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -f database/migrations/schema.sql
echo "✓ Schema applied"

echo ""
echo "=========================================="
echo "Database reset complete!"
echo "=========================================="
echo ""
echo "Database: $DB_NAME"
echo "Status: Ready for use"
echo ""