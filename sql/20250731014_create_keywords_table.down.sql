-- Drop audit trigger
DROP TRIGGER IF EXISTS keywords_audit_trigger ON public.keywords;

-- Drop audit trigger function
DROP FUNCTION IF EXISTS keywords_audit_trigger_func;

-- Drop audit table
DROP TABLE IF EXISTS keywords_audit;

-- Drop index on 'source' column (if it exists)
DROP INDEX IF EXISTS idx_keywords_source;

-- Drop main keywords table
DROP TABLE IF EXISTS keywords;

-- Drop ENUM type used in 'source' column
DROP TYPE IF EXISTS keyword_source;
