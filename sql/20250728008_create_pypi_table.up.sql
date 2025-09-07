-- Create pypi table

CREATE TABLE IF NOT EXISTS pypi (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL,
    project_name VARCHAR(128) NOT NULL,
    description VARCHAR NOT NULL,
    download_history JSONB,
    package_url VARCHAR(256) NOT NULL,
    project_url VARCHAR(256) NOT NULL,
    release_url VARCHAR(256) NOT NULL,
    github_url VARCHAR(256),
    author_name VARCHAR(256),
    author_email VARCHAR(128),
    package_version VARCHAR(32) NOT NULL,
    is_latest BOOLEAN NOT NULL,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(64) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMP,
    version INTEGER NOT NULL,
    CONSTRAINT fk_record
        FOREIGN KEY (record_id)
        REFERENCES records (id)
        ON DELETE CASCADE
);

-- Create indexes on pypi table

CREATE INDEX IF NOT EXISTS idx_pypi_project_name ON pypi(project_name);
CREATE INDEX IF NOT EXISTS idx_pypi_python_version ON pypi(python_version);

-- Create pypi audit table

CREATE TABLE IF NOT EXISTS pypi_audit (
    audit_id SERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    action_by VARCHAR(64),
    pypi_id INTEGER,
    record_id_before INTEGER,
    record_id_after INTEGER,
    project_name_before VARCHAR(128),
    project_name_after VARCHAR(128),
    description_before VARCHAR,
    description_after VARCHAR,
    download_history_before JSONB,
    download_history_after JSONB,
    package_url_before VARCHAR(256),
    package_url_after VARCHAR(256),
    project_url_before VARCHAR(256),
    project_url_after VARCHAR(256),
    release_url_before VARCHAR(256),
    release_url_after VARCHAR(256),
    github_url_before VARCHAR(256),
    github_url_after VARCHAR(256),
    author_name_before VARCHAR(256),
    author_name_after VARCHAR(256),
    author_email_before VARCHAR(128),
    author_email_after VARCHAR(128),
    package_version_before VARCHAR(32),
    package_version_after VARCHAR(32),
    is_latest_before BOOLEAN,
    is_latest_after BOOLEAN,
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
    UNIQUE(pypi_id,version_after)
);

-- Create indexes on pypi audit table

CREATE INDEX IF NOT EXISTS idx_pypi_audit_pypi_id ON pypi_audit(pypi_id);
CREATE INDEX IF NOT EXISTS idx_pypi_audit_action_tstamp ON pypi_audit(action_tstamp);

-- Create pypi audit trigger function

CREATE OR REPLACE FUNCTION pypi_audit_trigger_func()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $$
DECLARE
    v_action TEXT := TG_OP;
    v_action_by VARCHAR(64);
BEGIN
    IF v_action = 'INSERT' THEN
        v_action_by := current_user;
        INSERT INTO pypi_audit (
            action, action_by, pypi_id,
            record_id_after,
            project_name_after,
            description_after,
            download_history_after,
            package_url_after,
            project_url_after,
            release_url_after,
            github_url_after,
            author_name_after,
            author_email_after,
            package_version_after,
            is_latest_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            NEW.record_id,
            NEW.project_name,
            NEW.description,
            NEW.download_history,
            NEW.package_url,
            NEW.project_url,
            NEW.release_url,
            NEW.github_url,
            NEW.author_name,
            NEW.author_email,
            NEW.package_version,
            NEW.is_latest
        );
        RETURN NEW;

    ELSIF v_action = 'UPDATE' THEN
        v_action_by := current_user;
        INSERT INTO pypi_audit (
            action, action_by, pypi_id,
            record_id_before, record_id_after,
            project_name_before, project_name_after,
            description_before, description_after,
            download_history_before, download_history_after,
            package_url_before, package_url_after,
            project_url_before, project_url_after,
            release_url_before, release_url_after,
            github_url_before, github_url_after,
            author_name_before, author_name_after,
            author_email_before, author_email_after,
            package_version_before, package_version_after,
            is_latest_before, is_latest_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            OLD.record_id, NEW.record_id,
            OLD.project_name, NEW.project_name,
            OLD.description, NEW.description,
            OLD.download_history, NEW.download_history,
            OLD.package_url, NEW.package_url,
            OLD.project_url, NEW.project_url,
            OLD.release_url, NEW.release_url,
            OLD.github_url, NEW.github_url,
            OLD.author_name, NEW.author_name,
            OLD.author_email, NEW.author_email,
            OLD.package_version, NEW.package_version,
            OLD.is_latest, NEW.is_latest
        );
        RETURN NEW;

    ELSIF v_action = 'DELETE' THEN
        v_action_by := current_user;
        INSERT INTO pypi_audit (
            action, action_by, pypi_id,
            record_id_before,
            project_name_before,
            description_before,
            download_history_before,
            package_url_before,
            project_url_before,
            release_url_before,
            github_url_before,
            author_name_before,
            author_email_before,
            package_version_before,
            is_latest_before
        ) VALUES (
            v_action, v_action_by, OLD.id,
            OLD.record_id,
            OLD.project_name,
            OLD.description,
            OLD.download_history,
            OLD.package_url,
            OLD.project_url,
            OLD.release_url,
            OLD.github_url,
            OLD.author_name,
            OLD.author_email,
            OLD.package_version,
            OLD.is_latest
        );
        RETURN OLD;
    END IF;

    RAISE WARNING 'pypi_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Create pypi audit trigger

CREATE TRIGGER trg_audit_pypi
AFTER INSERT OR UPDATE OR DELETE ON pypi
FOR EACH ROW EXECUTE FUNCTION pypi_audit_trigger_func();
