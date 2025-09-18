-- Create main table

CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL,
    abstract TEXT NOT NULL,
    source_id VARCHAR NOT NULL,
    doi VARCHAR,
    status article_status NOT NULL,
    publish_date TIMESTAMP,
    link VARCHAR NOT NULL,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_by VARCHAR(64) NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMP,
    version INTEGER NOT NULL,
    CONSTRAINT fk_record
        FOREIGN KEY (record_id)
        REFERENCES records (id)
        ON DELETE CASCADE
);

-- Create indexes on main table


-- Create audit table

CREATE TABLE IF NOT EXISTS articles_audit (
    audit_id SERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    action_by VARCHAR(64),
    article_id INTEGER,
    record_id_before INTEGER,
    record_id_after INTEGER,
    abstract_before TEXT,
    abstract_after TEXT,
    source_id_before VARCHAR,
    source_id_after VARCHAR,
    doi_before VARCHAR,
    doi_after VARCHAR,
    status_before article_status,
    status_after article_status,
    publish_date_before TIMESTAMP,
    publish_date_after TIMESTAMP,
    link_before VARCHAR,
    link_after VARCHAR,
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
    UNIQUE(article_id,version_after)
);

-- Create indexes on audit table

CREATE INDEX IF NOT EXISTS idx_articles_audit_articles_id ON articles_audit(article_id);
CREATE INDEX IF NOT EXISTS idx_articles_audit_action_tstamp ON articles_audit(action_tstamp);

-- Create trigger function

CREATE OR REPLACE FUNCTION articles_audit_trigger_func()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $$
DECLARE
    v_action TEXT := TG_OP;
    v_action_by VARCHAR(64);
BEGIN
    IF v_action = 'INSERT' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO articles_audit (
            action, action_by, article_id,
            record_id_after, abstract_after, source_id_after, doi_after,
            status_after, publish_date_after, link_after,
            created_by_after, created_at_after,
            updated_by_after, updated_at_after,
            deleted_by_after, deleted_at_after,
            version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            NEW.record_id, NEW.abstract, NEW.source_id, NEW.doi,
            NEW.status, NEW.publish_date, NEW.link,
            NEW.created_by, NEW.created_at,
            NEW.updated_by, NEW.updated_at,
            NEW.deleted_by, NEW.deleted_at,
            NEW.version
        );
        RETURN NEW;

    ELSIF v_action = 'UPDATE' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO articles_audit (
            action, action_by, article_id,
            record_id_before, record_id_after,
            abstract_before, abstract_after,
            source_id_before, source_id_after,
            doi_before, doi_after,
            status_before, status_after,
            publish_date_before, publish_date_after,
            link_before, link_after,
            created_by_before, created_by_after,
            created_at_before, created_at_after,
            updated_by_before, updated_by_after,
            updated_at_before, updated_at_after,
            deleted_by_before, deleted_by_after,
            deleted_at_before, deleted_at_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            OLD.record_id, NEW.record_id,
            OLD.abstract, NEW.abstract,
            OLD.source_id, NEW.source_id,
            OLD.doi, NEW.doi,
            OLD.status, NEW.status,
            OLD.publish_date, NEW.publish_date,
            OLD.link, NEW.link,
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
        INSERT INTO articles_audit (
            action, action_by, article_id,
            record_id_before,
            abstract_before,
            source_id_before,
            doi_before,
            status_before,
            publish_date_before,
            link_before,
            created_by_before,
            created_at_before,
            updated_by_before,
            updated_at_before,
            deleted_by_before,
            deleted_at_before,
            version_before
        ) VALUES (
            v_action, v_action_by, OLD.id,
            OLD.record_id,
            OLD.abstract,
            OLD.source_id,
            OLD.doi,
            OLD.status,
            OLD.publish_date,
            OLD.link,
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

    RAISE WARNING 'articles_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Create trigger

CREATE TRIGGER trg_audit_articles
AFTER INSERT OR UPDATE OR DELETE ON articles
FOR EACH ROW EXECUTE FUNCTION articles_audit_trigger_func();
