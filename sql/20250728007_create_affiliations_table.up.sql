-- Create affiliations table

CREATE TABLE IF NOT EXISTS affiliations (
    id SERIAL PRIMARY KEY,
    author_id INTEGER NOT NULL,
    institute VARCHAR(128) NOT NULL,
    location VARCHAR(128),
    CONSTRAINT fk_author
        FOREIGN KEY (author_id)
        REFERENCES authors (id)
        ON DELETE CASCADE
);

-- Create indexes on affiliations table

CREATE INDEX IF NOT EXISTS idx_affiliations_author_id ON affiliations(author_id);
CREATE INDEX IF NOT EXISTS idx_affiliations_institute ON affiliations(institute);
CREATE INDEX IF NOT EXISTS idx_affiliations_location ON affiliations(location);

-- Create affiliations audit table

CREATE TABLE IF NOT EXISTS affiliations_audit (
    audit_id SERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    action_by VARCHAR(64),
    affiliation_id INTEGER,
    author_id_before INTEGER,
    author_id_after INTEGER,
    institute_before VARCHAR(128),
    institute_after VARCHAR(128),
    location_before VARCHAR(128),
    location_after VARCHAR(128),
    version_before INTEGER,
    version_after INTEGER,
    created_by_before VARCHAR(64),
    created_by_after VARCHAR(64),
    created_at_before TIMESTAMPTZ,
    created_at_after TIMESTAMPTZ,
    updated_by_before VARCHAR(64),
    updated_by_after VARCHAR(64),
    updated_at_before TIMESTAMPTZ,
    updated_at_after TIMESTAMPTZ,
    deleted_by_before VARCHAR(64),
    deleted_by_after VARCHAR(64),
    deleted_at_before TIMESTAMPTZ,
    deleted_at_after TIMESTAMPTZ,
    UNIQUE(affiliation_id,version_after)
);

-- Create indexes on affiliations audit table

CREATE INDEX IF NOT EXISTS idx_affiliations_audit_affiliations_id ON affiliations_audit(affiliation_id);
CREATE INDEX IF NOT EXISTS idx_affiliations_audit_action_tstamp ON affiliations_audit(action_tstamp);

-- Create affiliations audit trigger function

CREATE OR REPLACE FUNCTION affiliations_audit_trigger_func()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $$
DECLARE
    v_action TEXT := TG_OP;
    v_action_by VARCHAR(64);
BEGIN
    IF v_action = 'INSERT' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO affiliations_audit (
            action, action_by, affiliation_id,
            author_id_after, institute_after, location_after,
            created_by_after, created_at_after,
            updated_by_after, updated_at_after,
            deleted_by_after, deleted_at_after,
            version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            NEW.author_id, NEW.institute, NEW.location,
            NEW.created_by, NEW.created_at,
            NEW.updated_by, NEW.updated_at,
            NEW.deleted_by, NEW.deleted_at,
            NEW.version
        );
        RETURN NEW;

    ELSIF v_action = 'UPDATE' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO affiliations_audit (
            action, action_by, affiliation_id,
            author_id_before, author_id_after,
            institute_before, institute_after,
            location_before, location_after,
            created_by_before, created_by_after,
            created_at_before, created_at_after,
            updated_by_before, updated_by_after,
            updated_at_before, updated_at_after,
            deleted_by_before, deleted_by_after,
            deleted_at_before, deleted_at_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            OLD.author_id, NEW.author_id,
            OLD.institute, NEW.institute,
            OLD.location, NEW.location,
            OLD.created_by, NEW.created_by,
            OLD.created_at, NEW.created_at,
            OLD.updated_by, NEW.updated_by,
            OLD.updated_at, NEW.updated_at,
            OLD.deleted_by, NEW.deleted_by,
            OLD.deleted_at, NEW.deleted_at,
            OLD.version, NEW.version
        );
        RETURN NEW;

    ELSIF v_action = 'DELETE' THEN
        v_action_by := COALESCE(OLD.deleted_by, OLD.updated_by, OLD.created_by, current_user);
        INSERT INTO affiliations_audit (
            action, action_by, affiliation_id,
            author_id_before,
            institute_before,
            location_before,
            created_by_before,
            created_at_before,
            updated_by_before,
            updated_at_before,
            deleted_by_before,
            deleted_at_before,
            version_before
        ) VALUES (
            v_action, v_action_by, OLD.id,
            OLD.author_id,
            OLD.institute,
            OLD.location,
            OLD.created_by,
            OLD.created_at,
            OLD.updated_by,
            OLD.updated_at,
            OLD.deleted_by,
            OLD.deleted_at,
            OLD.version
        );
        RETURN OLD;
    END IF;

    RAISE WARNING 'affiliations_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Create affiliations audit trigger

CREATE TRIGGER trg_audit_affiliations
AFTER INSERT OR UPDATE OR DELETE ON affiliations
FOR EACH ROW EXECUTE FUNCTION affiliations_audit_trigger_func();
