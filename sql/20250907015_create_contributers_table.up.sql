-- Create contributers table
CREATE TABLE IF NOT EXISTS contributers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    contact VARCHAR(64) NOT NULL,
    username VARCHAR(64),
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(64) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMP,
    version INTEGER,
    CONSTRAINT fk_affiliations
        FOREIGN KEY (id)
        REFERENCES affiliations (contributer_id)
        ON DELETE CASCADE
);

-- Create indexes on contributers table
CREATE INDEX IF NOT EXISTS idx_contributers_name ON contributers(name);

-- Create contributers audit table
CREATE TABLE IF NOT EXISTS contributers_audit (
    audit_id SERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    action_by VARCHAR(64),
    contributer_id INTEGER,
    name_before VARCHAR(64),
    name_after VARCHAR(64),
    contact_before VARCHAR(64),
    contact_after VARCHAR(64),
    username_before VARCHAR(64),
    username_after VARCHAR(64),
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
    version_before INTEGER,
    version_after INTEGER,
    UNIQUE(contributer_id,version_after)
);

-- Create indexes on contributers audit table
CREATE INDEX IF NOT EXISTS idx_contributers_audit_contributer_id ON contributers_audit(contributer_id);
CREATE INDEX IF NOT EXISTS idx_contributers_audit_action_tstamp ON contributers_audit(action_tstamp);

-- Create contributers audit trigger function
CREATE OR REPLACE FUNCTION contributers_audit_trigger_func()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $$
DECLARE
    v_action TEXT := TG_OP;
    v_action_by VARCHAR(64);
BEGIN
    IF v_action = 'INSERT' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO contributers_audit (
            action, action_by, contributer_id,
            name_after, contact_after,
            created_by_after, created_at_after,
            updated_by_after, updated_at_after,
            deleted_by_after, deleted_at_after,
            version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            NEW.name, NEW.contact,
            NEW.created_by, NEW.created_at,
            NEW.updated_by, NEW.updated_at,
            NEW.deleted_by, NEW.deleted_at,
            NEW.version
        );
        RETURN NEW;

    ELSIF v_action = 'UPDATE' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO contributers_audit (
            action, action_by, contributer_id,
            name_before, name_after,
            contact_before, contact_after,
            created_by_before, created_by_after,
            created_at_before, created_at_after,
            updated_by_before, updated_by_after,
            updated_at_before, updated_at_after,
            deleted_by_before, deleted_by_after,
            deleted_at_before, deleted_at_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            OLD.name, NEW.name,
            OLD.contact, NEW.contact,
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
        INSERT INTO contributers_audit (
            action, action_by, contributer_id,
            name_before,
            contact_before,
            created_by_before,
            created_at_before,
            updated_by_before,
            updated_at_before,
            deleted_by_before,
            deleted_at_before,
            version_before
        ) VALUES (
            v_action, v_action_by, OLD.id,
            OLD.name,
            OLD.contact,
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

    RAISE WARNING 'contributers_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Create contributers audit trigger
CREATE TRIGGER trg_audit_contributers
AFTER INSERT OR UPDATE OR DELETE ON contributers
FOR EACH ROW EXECUTE FUNCTION contributers_audit_trigger_func();
