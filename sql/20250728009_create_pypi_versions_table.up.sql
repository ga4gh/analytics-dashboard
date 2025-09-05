-- Create main table pypi_versions

CREATE TABLE IF NOT EXISTS pypi_versions (
    id INTEGER NOT NULL,
    pypi_version VARCHAR(32) NOT NULL,
    python_version VARCHAR(32) NOT NULL,
    release_date TIMESTAMP,
    download_url VARCHAR(256) NOT NULL,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(64) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMP,
    version INTEGER NOT NULL,
    PRIMARY KEY (id, pypi_version),
    CONSTRAINT fk_pypi
        FOREIGN KEY (id)
        REFERENCES pypi (id)
        ON DELETE CASCADE
);

-- Indexes on main table

CREATE INDEX IF NOT EXISTS idx_pypi_versions_python_version ON pypi_versions(python_version);
CREATE INDEX IF NOT EXISTS idx_pypi_versions_release_date ON pypi_versions(release_date);

-- Audit table for pypi_versions

CREATE TABLE IF NOT EXISTS pypi_versions_audit (
    audit_id SERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    action_by VARCHAR(64),
    pypi_versions_id INTEGER NOT NULL,
    pypi_versions_pypi_version VARCHAR(32) NOT NULL,
    python_version_before VARCHAR(32),
    python_version_after VARCHAR(32),
    release_date_before TIMESTAMPTZ,
    release_date_after TIMESTAMPTZ,
    download_url_before VARCHAR(256)
    download_url_after VARCHAR(256)
    created_by_before VARCHAR(64),
    created_by_after VARCHAR(64),
    created_at_before TIMESTAMP,
    created_at_after TIMESTAMP,
    updated_by_before VARCHAR(64),
    updated_by_after VARCHAR(64),
    updated_at_before TIMESTAMP,
    updated_at_after TIMESTAMP,
    deleted_by_before VARCHAR(64),
    deleted_by_after VARCHAR(64),
    deleted_at_before TIMESTAMP,
    deleted_at_after TIMESTAMP,
    version_before INTEGER,
    version_after INTEGER,
    UNIQUE(pypi_versions_id,version_after)
);

-- Indexes on audit table

CREATE INDEX IF NOT EXISTS idx_pypi_versions_audit_pypi_versions_id ON pypi_versions_audit(pypi_versions_id);
CREATE INDEX IF NOT EXISTS idx_pypi_versions_audit_action_tstamp ON pypi_versions_audit(action_tstamp);

-- Trigger function for audit

CREATE OR REPLACE FUNCTION pypi_versions_audit_trigger_func()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $$
DECLARE
    v_action TEXT := TG_OP;
    v_action_by VARCHAR(64);
BEGIN
    IF v_action = 'INSERT' THEN
        v_action_by := current_user;
        INSERT INTO pypi_versions_audit (
            action, action_by, pypi_versions_id, pypi_versions_pypi_version,
            python_version_after, release_date_after, download_url_after
        ) VALUES (
            v_action, v_action_by, NEW.id, NEW.pypi_version,
            NEW.python_version, NEW.release_date, NEW.download_url
        );
        RETURN NEW;

    ELSIF v_action = 'UPDATE' THEN
        v_action_by := current_user;
        INSERT INTO pypi_versions_audit (
            action, action_by, pypi_versions_id, pypi_versions_pypi_version,
            python_version_before, python_version_after,
            release_date_before, release_date_after,
            download_url_before, download_url_after
        ) VALUES (
            v_action, v_action_by, NEW.id, NEW.pypi_version,
            OLD.python_version, NEW.python_version,
            OLD.release_date, NEW.release_date,
            OLD.download_url, NEW.download_url
        );
        RETURN NEW;

    ELSIF v_action = 'DELETE' THEN
        v_action_by := current_user;
        INSERT INTO pypi_versions_audit (
            action, action_by, pypi_versions_id, pypi_versions_pypi_version,
            python_version_before, release_date_before, download_url_before
        ) VALUES (
            v_action, v_action_by, OLD.id, OLD.pypi_version,
            OLD.python_version, OLD.release_date, OLD.download_url
        );
        RETURN OLD;
    END IF;

    RAISE WARNING 'pypi_versions_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Attach trigger

CREATE TRIGGER trg_audit_pypi_versions
AFTER INSERT OR UPDATE OR DELETE ON pypi_versions
FOR EACH ROW EXECUTE FUNCTION pypi_versions_audit_trigger_func();
