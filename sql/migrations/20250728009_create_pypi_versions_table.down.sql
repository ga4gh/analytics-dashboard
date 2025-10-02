DROP TRIGGER IF EXISTS trg_audit_pypi_versions ON public.pypi_versions;
DROP FUNCTION IF EXISTS pypi_versions_audit_trigger_func;
DROP TABLE IF EXISTS pypi_versions_audit;
DROP INDEX IF EXISTS idx_pypi_versions_audit_pypi_versions_id;
DROP INDEX IF EXISTS idx_pypi_versions_audit_action_tstamp;
DROP INDEX IF EXISTS idx_pypi_versions_python_version;
DROP INDEX IF EXISTS idx_pypi_versions_release_date;
DROP TABLE IF EXISTS pypi_versions;
