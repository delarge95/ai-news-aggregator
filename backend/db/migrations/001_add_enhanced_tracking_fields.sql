-- Migration: Add Enhanced Tracking Fields
-- Description: Agrega campos de tracking mejorado para duplicados, APIs y cache
-- Date: 2025-11-06

-- =====================================================
-- Updates to Source Table
-- =====================================================

-- Add api_source_id field to track specific API source IDs
ALTER TABLE sources 
ADD COLUMN api_source_id VARCHAR(255);

-- Add rate_limit_info field to track API usage
ALTER TABLE sources 
ADD COLUMN rate_limit_info JSONB;

-- Create index for api_source_id
CREATE INDEX idx_sources_api_source_id ON sources(api_source_id);

-- =====================================================
-- Updates to Article Table  
-- =====================================================

-- Add duplicate_group_id field for tracking duplicate articles
ALTER TABLE articles 
ADD COLUMN duplicate_group_id UUID;

-- Add content_hash field for duplicate detection (SHA-256)
ALTER TABLE articles 
ADD COLUMN content_hash VARCHAR(64);

-- Add cache_expires_at field for cache management
ALTER TABLE articles 
ADD COLUMN cache_expires_at TIMESTAMP WITH TIME ZONE;

-- Create indexes for performance
CREATE INDEX idx_articles_duplicate_group_id ON articles(duplicate_group_id);
CREATE INDEX idx_articles_content_hash ON articles(content_hash);
CREATE INDEX idx_articles_cache_expires_at ON articles(cache_expires_at);

-- Create composite index for duplicate detection
CREATE INDEX idx_articles_duplicate_group_hash ON articles(duplicate_group_id, content_hash);

-- =====================================================
-- ROLLBACK SCRIPT
-- =====================================================
-- To rollback these changes, run:

-- Remove indexes
DROP INDEX IF EXISTS idx_sources_api_source_id;
DROP INDEX IF EXISTS idx_articles_duplicate_group_id;
DROP INDEX IF EXISTS idx_articles_content_hash;
DROP INDEX IF EXISTS idx_articles_cache_expires_at;
DROP INDEX IF EXISTS idx_articles_duplicate_group_hash;

-- Remove columns
ALTER TABLE sources DROP COLUMN IF EXISTS api_source_id;
ALTER TABLE sources DROP COLUMN IF EXISTS rate_limit_info;
ALTER TABLE articles DROP COLUMN IF EXISTS duplicate_group_id;
ALTER TABLE articles DROP COLUMN IF EXISTS content_hash;
ALTER TABLE articles DROP COLUMN IF EXISTS cache_expires_at;