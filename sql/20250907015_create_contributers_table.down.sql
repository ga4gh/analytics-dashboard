DROP TRIGGER IF EXISTS trg_audit_contributers ON public.contributers;
DROP FUNCTION IF EXISTS contributers_audit_trigger_func;
DROP TABLE IF EXISTS contributers_audit;
DROP INDEX IF EXISTS idx_contributers_name;
DROP TABLE IF EXISTS contributers;
