-- Drop audit trigger
DROP TRIGGER IF EXISTS repo_entity_actions_audit_trigger ON public.repo_entity_actions;

-- Drop audit trigger function
DROP FUNCTION IF EXISTS repo_entity_actions_audit_trigger_func;

-- Drop audit table
DROP TABLE IF EXISTS repo_entity_actions_audit;

-- Drop unused index (was not created in the latest up file)
DROP INDEX IF EXISTS idx_repo_entity_actions_source;

-- Drop main table
DROP TABLE IF EXISTS repo_entity_actions;

-- Drop ENUM type
DROP TYPE IF EXISTS repo_action_type;