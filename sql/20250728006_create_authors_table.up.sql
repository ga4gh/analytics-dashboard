-- Create authors table

CREATE TABLE IF NOT EXISTS authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    contact VARCHAR(64) NOT NULL,
    is_primary BOOLEAN NOT NULL,
    article_type article_type NOT NULL,
    article_id INTEGER,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(64) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMP,
    version INTEGER NOT NULL,
    CONSTRAINT fk_article
        FOREIGN KEY (article_id)
        REFERENCES articles (id)
        ON DELETE CASCADE
);

-- Create indexes on authors table

CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(name);
CREATE INDEX IF NOT EXISTS idx_authors_is_primary ON authors(is_primary);

-- Create authors audit table

CREATE TABLE IF NOT EXISTS authors_audit (
    audit_id SERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    action_by VARCHAR(64),
    author_id INTEGER,
    name_before VARCHAR(64),
    name_after VARCHAR(64),
    contact_before VARCHAR(64),
    contact_after VARCHAR(64),
    is_primary_before BOOLEAN,
    is_primary_after BOOLEAN,
    article_type_before article_type,
    article_type_after article_type,
    article_id_before INTEGER,
    article_id_after INTEGER,
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
    UNIQUE(author_id,version_after)
);

-- Create indexes on authors audit table

CREATE INDEX IF NOT EXISTS idx_authors_audit_author_id ON authors_audit(author_id);
CREATE INDEX IF NOT EXISTS idx_authors_audit_action_tstamp ON authors_audit(action_tstamp);

-- Create authors audit trigger function

CREATE OR REPLACE FUNCTION authors_audit_trigger_func()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $$
DECLARE
    v_action TEXT := TG_OP;
    v_action_by VARCHAR(64);
BEGIN
    IF v_action = 'INSERT' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO authors_audit (
            action, action_by, author_id,
            name_after, contact_after, is_primary_after,
            article_type_after, article_id_after,
            created_by_after, created_at_after,
            updated_by_after, updated_at_after,
            deleted_by_after, deleted_at_after,
            version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            NEW.name, NEW.contact, NEW.is_primary,
            NEW.article_type, NEW.article_id,
            NEW.created_by, NEW.created_at,
            NEW.updated_by, NEW.updated_at,
            NEW.deleted_by, NEW.deleted_at,
            NEW.version
        );
        RETURN NEW;

    ELSIF v_action = 'UPDATE' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO authors_audit (
            action, action_by, author_id,
            name_before, name_after,
            contact_before, contact_after,
            is_primary_before, is_primary_after,
            article_type_before, article_type_after,
            article_id_before, article_id_after,
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
            OLD.is_primary, NEW.is_primary,
            OLD.article_type, NEW.article_type,
            OLD.article_id, NEW.article_id,
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
        INSERT INTO authors_audit (
            action, action_by, author_id,
            name_before,
            contact_before,
            is_primary_before,
            article_type_before,
            article_id_before,
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
            OLD.is_primary,
            OLD.article_type,
            OLD.article_id,
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

    RAISE WARNING 'authors_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Create authors audit trigger

CREATE TRIGGER trg_audit_authors
AFTER INSERT OR UPDATE OR DELETE ON authors
FOR EACH ROW EXECUTE FUNCTION authors_audit_trigger_func();
