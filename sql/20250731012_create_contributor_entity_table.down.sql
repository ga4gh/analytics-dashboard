-- Drop audit trigger
DROP TRIGGER IF EXISTS contributor_entity_audit_trigger ON public.contributor_entity;

-- Drop audit trigger function
DROP FUNCTION IF EXISTS contributor_entity_audit_trigger_func;

-- Drop audit table
DROP TABLE IF EXISTS contributor_entity_audit;

-- Drop index on 'source' column (if it exists)
DROP INDEX IF EXISTS idx_contributor_entity_source;

-- Drop main contributor_entity table
DROP TABLE IF EXISTS contributor_entity;

-- Drop ENUM type used in 'type' column
DROP TYPE IF EXISTS contributor_entity_type;
