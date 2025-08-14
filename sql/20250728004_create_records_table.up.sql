-- Create main table

CREATE TABLE IF NOT EXISTS records (
  	id SERIAL PRIMARY KEY,
  	record_type record_type NOT NULL,
  	source source NOT NULL,
  	status status NOT NULL,
  	created_by VARCHAR(64) NOT NULL,
  	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  	updated_by VARCHAR(64) NOT NULL,
  	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  	deleted_by VARCHAR(64),
  	deleted_at TIMESTAMPTZ,
  	version INTEGER
);

-- Create main table indexes


-- Create Audit table

CREATE TABLE IF NOT EXISTS records_audit (
    audit_id SERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    action_by VARCHAR(64),
    record_id INTEGER,
    record_type_before record_type,
    record_type_after record_type,
    source_before source,
    source_after source,
    status_before status,
    status_after status,
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
    UNIQUE(record_id, version_after)
);

-- Create audit table indexes


-- Trigger function

CREATE OR REPLACE FUNCTION records_audit_trigger_func()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $$
DECLARE
    v_action TEXT := TG_OP;
    v_action_by VARCHAR(64);
BEGIN
    IF v_action = 'INSERT' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO records_audit (
            action, action_by, record_id,
            record_type_after, source_after, status_after,
            created_by_after, created_at_after,
            updated_by_after, updated_at_after,
            deleted_by_after, deleted_at_after,
            version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            NEW.record_type, NEW.source, NEW.status,
            NEW.created_by, NEW.created_at,
            NEW.updated_by, NEW.updated_at,
            NEW.deleted_by, NEW.deleted_at,
            NEW.version
        );
        RETURN NEW;

    ELSIF v_action = 'UPDATE' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO records_audit (
            action, action_by, record_id,
            record_type_before, record_type_after,
            source_before, source_after,
            status_before, status_after,
            created_by_before, created_by_after,
            created_at_before, created_at_after,
            updated_by_before, updated_by_after,
            updated_at_before, updated_at_after,
            deleted_by_before, deleted_by_after,
            deleted_at_before, deleted_at_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            OLD.record_type, NEW.record_type,
            OLD.source, NEW.source,
            OLD.status, NEW.status,
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
        INSERT INTO records_audit (
            action, action_by, record_id,
            record_type_before,
            source_before,
            status_before,
            created_by_before,
            created_at_before,
            updated_by_before,
            updated_at_before,
            deleted_by_before,
            deleted_at_before,
            version_before
        ) VALUES (
            v_action, v_action_by, OLD.id,
            OLD.record_type,
            OLD.source,
            OLD.status,
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

    RAISE WARNING 'records_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Attach Trigger

CREATE TRIGGER trg_audit_records
AFTER INSERT OR UPDATE OR DELETE ON public.records
FOR EACH ROW EXECUTE FUNCTION records_audit_trigger_func();