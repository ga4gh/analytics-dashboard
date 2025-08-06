-- Drop audit trigger
DROP TRIGGER IF EXISTS github_archieved_stats_audit_trigger ON public.github_archieved_stats;

-- Drop audit trigger function
DROP FUNCTION IF EXISTS github_archieved_stats_audit_trigger_func;

-- Drop audit table
DROP TABLE IF EXISTS github_archieved_stats_audit;

-- Drop main github_archieved_stats table
DROP TABLE IF EXISTS github_archieved_stats;
