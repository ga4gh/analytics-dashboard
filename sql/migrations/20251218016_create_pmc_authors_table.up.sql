CREATE TABLE IF NOT EXISTS pmc_authors (
    id SERIAL PRIMARY KEY,
    fullname TEXT NOT NULL,
    firstname VARCHAR(128),
    lastname VARCHAR(128),
    initials VARCHAR(32),
    orcid VARCHAR(64),
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(64),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_pmc_authors_lastname ON pmc_authors(lastname);
CREATE INDEX IF NOT EXISTS idx_pmc_authors_orcid ON pmc_authors(orcid);
