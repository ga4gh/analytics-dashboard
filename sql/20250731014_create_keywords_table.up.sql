-- Create ENUM type
CREATE TYPE keyword_source AS ENUM ('github', 'pubmed', 'pypi');

-- Main table
CREATE TABLE keywords (
    id BIGSERIAL PRIMARY KEY, 
    name VARCHAR NOT NULL, 
    acronym VARCHAR NOT NULL, 
    source keyword_source,
    created_by VARCHAR(64) NOT NULL,
  	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  	updated_by VARCHAR(64) NOT NULL,
  	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  	deleted_by VARCHAR(64),
  	deleted_at TIMESTAMPTZ,
  	version INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_keywords_source ON keywords(source);

-- Audit table
CREATE TABLE keywords_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
    action_by TEXT,
    keywords_id INTEGER,
    name_before            VARCHAR,
    name_after             VARCHAR,
    acronym_before         VARCHAR,
    acronym_after          VARCHAR,
    source_before          VARCHAR,
    source_after           VARCHAR,
    created_at_before      TIMESTAMPTZ,
    created_at_after       TIMESTAMPTZ,
    created_by_before      VARCHAR,
    created_by_after       VARCHAR,
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

    UNIQUE(keywords_id, version_after)
);

-- Trigger function
CREATE OR REPLACE FUNCTION keywords_audit_trigger_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_action    TEXT := TG_OP;  -- 'INSERT' | 'UPDATE' | 'DELETE'
    v_action_by TEXT := current_user;
BEGIN
    IF v_action = 'INSERT' THEN
        INSERT INTO keywords_audit (
            action, action_by, keywords_id,
            name_before, name_after,
            acronym_before, acronym_after,
            source_before, source_after,
            created_at_before, created_at_after,
            created_by_before, created_by_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            NULL, NEW.name,
            NULL, NEW.acronym,
            NULL, NEW.source,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL
        );
        RETURN NEW;

    ELSIF v_action = 'UPDATE' THEN
        INSERT INTO keywords_audit (
            action, action_by, keywords_id,
            name_before, name_after,
            acronym_before, acronym_after,
            source_before, source_after,
            created_at_before, created_at_after,
            created_by_before, created_by_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            OLD.name, NEW.name,
            OLD.acronym, NEW.acronym,
            OLD.source, NEW.source,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL
        );
        RETURN NEW;

    ELSIF v_action = 'DELETE' THEN
        INSERT INTO keywords_audit (
            action, action_by, keywords_id,
            name_before, name_after,
            acronym_before, acronym_after,
            source_before, source_after,
            created_at_before, created_at_after,
            created_by_before, created_by_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, OLD.id,
            OLD.name, NULL,
            OLD.acronym, NULL,
            OLD.source, NULL,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL,
            NULL, NULL
        );
        RETURN OLD;
    END IF;

    RAISE WARNING 'keywords_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Trigger binding
CREATE TRIGGER keywords_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.keywords
FOR EACH ROW EXECUTE FUNCTION keywords_audit_trigger_func();
