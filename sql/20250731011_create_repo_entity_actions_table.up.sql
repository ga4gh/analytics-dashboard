-- Create ENUM type
CREATE TYPE repo_action_type AS ENUM ('star', 'watch', 'collaborator');

-- Main table
CREATE TABLE repo_entity_actions (
    id BIGSERIAL PRIMARY KEY, 
    repo_id BIGINT REFERENCES github_repos(id), 
    action_type repo_action_type NOT NULL,
    user_id BIGINT NOT NULL
);

-- Audit table
CREATE TABLE repo_entity_actions_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
    action_by TEXT,
    repo_entity_actions_id BIGINT,
    repo_id_before         VARCHAR NOT NULL,
    repo_id_after          VARCHAR NOT NULL,
    action_type_before     VARCHAR NOT NULL,
    action_type_after      VARCHAR NOT NULL,  
    user_id_before         VARCHAR NOT NULL, 
    user_id_after          VARCHAR NOT NULL,
    updated_at_before      TIMESTAMPTZ,
    updated_at_after       TIMESTAMPTZ,
    updated_by_before      VARCHAR,
    updated_by_after       VARCHAR,
    deleted_at_before      TIMESTAMPTZ,
    deleted_at_after       TIMESTAMPTZ,
    deleted_by_before      VARCHAR,
    deleted_by_after       VARCHAR,
    version_before         INT,
    version_after          INT,

    UNIQUE(repo_entity_actions_id, version_after)
);

-- Trigger function
CREATE OR REPLACE FUNCTION repo_entity_actions_audit_trigger_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_action       TEXT := TG_OP;  -- 'INSERT' | 'UPDATE' | 'DELETE'
    v_action_by    TEXT;
    v_next_version INT;
BEGIN
    -- determine next version
    SELECT COALESCE(MAX(version_after), 0) + 1 INTO v_next_version
    FROM repo_entity_actions_audit
    WHERE repo_entity_actions_id = COALESCE(NEW.id, OLD.id);

    IF v_action = 'INSERT' THEN
        v_action_by := current_user;
        INSERT INTO repo_entity_actions_audit (
            action, action_by, repo_entity_actions_id,
            repo_id_before, repo_id_after,
            action_type_before, action_type_after,
            user_id_before, user_id_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            NULL, NEW.repo_id,
            NULL, NEW.action_type,
            NULL, NEW.user_id,
            NULL, current_timestamp,
            NULL, v_action_by,
            NULL, NULL,
            NULL, NULL,
            NULL, v_next_version
        );
        RETURN NEW;

    ELSIF v_action = 'UPDATE' THEN
        v_action_by := current_user;
        INSERT INTO repo_entity_actions_audit (
            action, action_by, repo_entity_actions_id,
            repo_id_before, repo_id_after,
            action_type_before, action_type_after,
            user_id_before, user_id_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            OLD.repo_id, NEW.repo_id,
            OLD.action_type, NEW.action_type,
            OLD.user_id, NEW.user_id,
            current_timestamp, current_timestamp,
            v_action_by, v_action_by,
            NULL, NULL,
            NULL, NULL,
            v_next_version - 1, v_next_version
        );
        RETURN NEW;

    ELSIF v_action = 'DELETE' THEN
        v_action_by := current_user;
        INSERT INTO repo_entity_actions_audit (
            action, action_by, repo_entity_actions_id,
            repo_id_before, repo_id_after,
            action_type_before, action_type_after,
            user_id_before, user_id_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, OLD.id,
            OLD.repo_id, NULL,
            OLD.action_type, NULL,
            OLD.user_id, NULL,
            current_timestamp, NULL,
            v_action_by, NULL,
            current_timestamp, current_timestamp,
            v_action_by, v_action_by,
            v_next_version - 1, v_next_version
        );
        RETURN OLD;
    END IF;

    RAISE WARNING 'repo_entity_actions_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Trigger binding
CREATE TRIGGER repo_entity_actions_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.repo_entity_actions
FOR EACH ROW EXECUTE FUNCTION repo_entity_actions_audit_trigger_func();
