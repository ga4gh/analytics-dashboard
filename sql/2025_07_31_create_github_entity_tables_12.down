-- Drop audit trigger
DROP TRIGGER IF EXISTS github_entity_audit_trigger ON public.github_entity;

-- Drop audit trigger function
DROP FUNCTION IF EXISTS github_entity_audit_trigger_func;

-- Drop audit table
DROP TABLE IF EXISTS github_entity_audit;

-- Drop index on 'source' column (if it exists)
DROP INDEX IF EXISTS idx_github_entity_source;

-- Drop main github_entity table
DROP TABLE IF EXISTS github_entity;

-- Drop ENUM type used in 'type' column
DROP TYPE IF EXISTS github_entity_type;
