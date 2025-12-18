CREATE TABLE IF NOT EXISTS pmc_articles (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL,
    source VARCHAR(64) NOT NULL,
    pm_id VARCHAR(64),
    pmc_id VARCHAR(64) NOT NULL,
    full_text_id VARCHAR(128) NOT NULL,
    doi VARCHAR(64) NOT NULL,
    title TEXT NOT NULL NOT NULL,
    pub_year INTEGER NOT NULL,
    abstract_text TEXT NOT NULL,
    affiliation TEXT NOT NULL,
    publication_status VARCHAR(64) NOT NULL,
    language VARCHAR(32) NOT NULL,
    pub_type VARCHAR(64),
    is_open_access BOOLEAN DEFAULT FALSE,
    inepmc BOOLEAN DEFAULT FALSE,
    inpmc BOOLEAN DEFAULT FALSE,
    has_pdf BOOLEAN DEFAULT FALSE,
    has_book BOOLEAN DEFAULT FALSE,
    has_suppl BOOLEAN DEFAULT FALSE,
    cited_by_count INTEGER DEFAULT 0,
    has_references BOOLEAN DEFAULT FALSE,
    date_of_creation TIMESTAMPTZ NOT NULL,
    first_index_date TIMESTAMPTZ NOT NULL,
    fulltext_receive_date TIMESTAMPTZ NOT NULL,
    revision_date TIMESTAMPTZ NOT NULL,
    epub_date TIMESTAMPTZ NOT NULL,
    first_publication_date TIMESTAMPTZ NOT NULL,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(64),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_pmc_articles_record
      FOREIGN KEY (record_id)
      REFERENCES records (id)
      ON DELETE CASCADE
);

-- Useful indexes (adjust/add based on query patterns)
CREATE INDEX IF NOT EXISTS idx_pmc_articles_record_id ON pmc_articles(record_id);
CREATE INDEX IF NOT EXISTS idx_pmc_articles_pm_id ON pmc_articles(pm_id);
CREATE INDEX IF NOT EXISTS idx_pmc_articles_pmc_id ON pmc_articles(pmc_id);
CREATE INDEX IF NOT EXISTS idx_pmc_articles_doi ON pmc_articles(doi);
CREATE INDEX IF NOT EXISTS idx_pmc_articles_pub_year ON pmc_articles(pub_year);
CREATE INDEX IF NOT EXISTS idx_pmc_articles_is_open_access ON pmc_articles(is_open_access);

-- Example COPY command to load CSV (adjust path and options as needed)
-- COPY pmc_articles(record_id, source, pm_id, pmc_id, full_text_id, doi, title, pub_year, abstract_text, affiliation,
--                   publication_status, language, pub_type, is_open_access, inepmc, inpmc, has_pdf, has_book, has_suppl,
--                   cited_by_count, has_references, date_of_creation, first_index_date, fulltext_receive_date,
--                   revision_date, epub_date, first_publication_date)
-- FROM '/full/path/to/your/pmc_articles.csv' WITH (FORMAT csv, HEADER true, NULL '');

-- Notes:
-- - Adjust VARCHAR lengths to suit your data.
-- - If pm_id/pmc_id should be unique, add UNIQUE(pm_id) / UNIQUE(pmc_id) constraints.
-- - Remove created_by/updated_by/etc if you don't need audit/metadata columns.