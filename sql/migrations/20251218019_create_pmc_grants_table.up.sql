CREATE TABLE IF NOT EXISTS grants (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL,
    grant_id VARCHAR(128),
    ingestion_id INTEGER NOT NULL,
    agency TEXT,
    family_name TEXT,
    given_name TEXT,
    initials TEXT,
    alias TEXT[],
    orcid TEXT,
    funder_name TEXT,
    doi TEXT,
    title TEXT,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    institution_name TEXT,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(64),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_grants_record
      FOREIGN KEY (record_id)
      REFERENCES records (id)
      ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_grants_record_id ON grants(record_id);
CREATE INDEX IF NOT EXISTS idx_grants_grant_id ON grants(grant_id);
CREATE INDEX IF NOT EXISTS idx_grants_agency ON grants(agency);