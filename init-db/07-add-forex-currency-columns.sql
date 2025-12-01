-- ============================================================================
-- Migration: Add base_currency and quote_currency columns to forex_rates table
-- ============================================================================
-- This migration adds base_currency and quote_currency columns to the forex_rates
-- table to store currency pair information directly with each rate record.
--
-- Date: 2025-12-01
-- ============================================================================

-- Add base_currency column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'forex_rates' 
        AND column_name = 'base_currency'
    ) THEN
        ALTER TABLE forex_rates 
        ADD COLUMN base_currency VARCHAR(10);
        
        COMMENT ON COLUMN forex_rates.base_currency IS 'Base currency code (e.g., USD, EUR, BTC)';
    END IF;
END $$;

-- Add quote_currency column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'forex_rates' 
        AND column_name = 'quote_currency'
    ) THEN
        ALTER TABLE forex_rates 
        ADD COLUMN quote_currency VARCHAR(10);
        
        COMMENT ON COLUMN forex_rates.quote_currency IS 'Quote currency code (e.g., USD, EUR)';
    END IF;
END $$;

-- Note: Existing records will have NULL values for these columns
-- This is acceptable as they are optional metadata fields

