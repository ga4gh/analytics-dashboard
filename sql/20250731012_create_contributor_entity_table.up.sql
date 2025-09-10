-- Create ENUM type
CREATE TYPE contributor_entity_type AS ENUM ('user', 'bot');

-- Main table
CREATE TABLE contributor_entity (
    id UUID PRIMARY KEY, 
    name VARCHAR NOT NULL, 
    user_id VARCHAR NOT NULL, 
    company VARCHAR, 
    email VARCHAR, 
    location VARCHAR, 
    type contributor_entity_type NOT NULL,
    created_by VARCHAR(64) NOT NULL,
  	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  	updated_by VARCHAR(64) NOT NULL,
  	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  	deleted_by VARCHAR(64),
  	deleted_at TIMESTAMPTZ,
  	version INTEGER NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_contributor_entity_location ON contributor_entity(location);
CREATE INDEX IF NOT EXISTS idx_contributor_entity_type ON contributor_entity(type);

-- Audit table
CREATE TABLE contributor_entity_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
    action_by TEXT,
    contributor_entity_id INTEGER,
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
    type_before            contributor_entity_type NOT NULL,
    type_after             contributor_entity_type NOT NULL,
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

    UNIQUE(contributor_entity_id, version_after)
);

-- Trigger function
CREATE OR REPLACE FUNCTION contributor_entity_audit_trigger_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_action    TEXT := TG_OP;  -- 'INSERT' | 'UPDATE' | 'DELETE'
    v_action_by TEXT;
BEGIN
    IF v_action = 'INSERT' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO contributor_entity_audit (
            action, action_by, contributor_entity_id,
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
        INSERT INTO contributor_entity_audit (
            action, action_by, contributor_entity_id,
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
        INSERT INTO contributor_entity_audit (
            action, action_by, contributor_entity_id,
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

    RAISE WARNING 'contributor_entity_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Trigger binding
CREATE TRIGGER contributor_entity_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.contributor_entity
FOR EACH ROW EXECUTE FUNCTION contributor_entity_audit_trigger_func();
