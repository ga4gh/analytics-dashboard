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

ALTER TABLE records_audit 
DROP COLUMN IF EXISTS keyword_before,
DROP COLUMN IF EXISTS keyword_after,
DROP COLUMN IF EXISTS product_line_before,
DROP COLUMN IF EXISTS product_line_after;

DROP INDEX IF EXISTS idx_records_keyword;
DROP INDEX IF EXISTS idx_records_product_line;

ALTER TABLE records DROP COLUMN IF EXISTS keyword;
ALTER TABLE records DROP COLUMN IF EXISTS product_line;