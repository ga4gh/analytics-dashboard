-- Create ENUM type
CREATE TYPE github_entity_type AS ENUM ('user', 'bot');

-- Main table
CREATE TABLE github_entity (
    id UUID PRIMARY KEY, 
    name VARCHAR NOT NULL, 
    user_id VARCHAR NOT NULL, 
    company VARCHAR NOT NULL, 
    email VARCHAR NOT NULL, 
    location VARCHAR, 
    type github_entity_type NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_github_entity_company ON github_entity(company);
CREATE INDEX IF NOT EXISTS idx_github_entity_location ON github_entity(location);
CREATE INDEX IF NOT EXISTS idx_github_entity_type ON github_entity(type);

-- Audit table
CREATE TABLE github_entity_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
    action_by TEXT,
    github_entity_id INTEGER,
    name_before            VARCHAR NOT NULL, 
    name_after             VARCHAR NOT NULL, 
    user_id_before         VARCHAR NOT NULL, 
    user_id_after          VARCHAR NOT NULL,
    company_before         VARCHAR NOT NULL,
    company_after          VARCHAR NOT NULL, 
    email_before           VARCHAR NOT NULL,
    email_after            VARCHAR NOT NULL, 
    location_before        VARCHAR,
    location_after         VARCHAR,  
    type_before            github_entity_type NOT NULL,
    type_after             github_entity_type NOT NULL,
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

    UNIQUE(github_entity_id, version_after)
);

-- Trigger function
CREATE OR REPLACE FUNCTION github_entity_audit_trigger_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_action    TEXT := TG_OP;  -- 'INSERT' | 'UPDATE' | 'DELETE'
    v_action_by TEXT;
BEGIN
    IF v_action = 'INSERT' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO github_entity_audit (
            action, action_by, github_entity_id,
            name_before, name_after,
            user_id_before, user_id_after,
            company_before, company_after,
            email_before, email_after,
            location_before, location_after,
            type_before, type_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            NULL, NEW.name,
            NULL, NEW.user_id,
            NULL, NEW.company,
            NULL, NEW.email,
            NULL, NEW.location,
            NULL, NEW.type,
            NULL, NEW.updated_at,
            NULL, NEW.updated_by,
            NULL, NEW.deleted_at,
            NULL, NEW.deleted_by,
            NULL, NEW.version
        );
        RETURN NEW;

    ELSIF v_action = 'UPDATE' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO github_entity_audit (
            action, action_by, github_entity_id,
            name_before, name_after,
            user_id_before, user_id_after,
            company_before, company_after,
            email_before, email_after,
            location_before, location_after,
            type_before, type_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            OLD.name, NEW.name,
            OLD.user_id, NEW.user_id,
            OLD.company, NEW.company,
            OLD.email, NEW.email,
            OLD.location, NEW.location,
            OLD.type, NEW.type,
            OLD.updated_at, NEW.updated_at,
            OLD.updated_by, NEW.updated_by,
            OLD.deleted_at, NEW.deleted_at,
            OLD.deleted_by, NEW.deleted_by,
            OLD.version, NEW.version
        );
        RETURN NEW;

    ELSIF v_action = 'DELETE' THEN
        v_action_by := COALESCE(OLD.deleted_by, OLD.updated_by, OLD.created_by, current_user);
        INSERT INTO github_entity_audit (
            action, action_by, github_entity_id,
            name_before, name_after,
            user_id_before, user_id_after,
            company_before, company_after,
            email_before, email_after,
            location_before, location_after,
            type_before, type_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, OLD.id,
            OLD.name, NULL,
            OLD.user_id, NULL,
            OLD.company, NULL,
            OLD.email, NULL,
            OLD.location, NULL,
            OLD.type, NULL,
            OLD.updated_at, NULL,
            OLD.updated_by, NULL,
            OLD.deleted_at, NULL,
            OLD.deleted_by, NULL,
            OLD.version, NULL
        );
        RETURN OLD;
    END IF;

    RAISE WARNING 'github_entity_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Trigger binding
CREATE TRIGGER github_entity_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.github_entity
FOR EACH ROW EXECUTE FUNCTION github_entity_audit_trigger_func();
