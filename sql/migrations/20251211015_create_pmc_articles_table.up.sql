CREATE TABLE IF NOT EXISTS pmc_articles (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL,
    ingestion_id INTEGER,
    source VARCHAR(64) NOT NULL,
    pm_id VARCHAR(64),
    pmc_id VARCHAR(64) NOT NULL,
    full_text_id VARCHAR(128) NOT NULL,
    doi VARCHAR(64) NOT NULL,
    title TEXT NOT NULL,
    pub_year INTEGER NOT NULL,
    abstract_text TEXT NOT NULL,
    affiliation TEXT NOT NULL,
    publication_status VARCHAR(64) NOT NULL,
    language VARCHAR(32) NOT NULL,
    pub_type JSONB,
    is_open_access VARCHAR(8) DEFAULT 'False',
    inepmc VARCHAR(8) DEFAULT 'False',
    inpmc VARCHAR(8) DEFAULT 'False',
    has_pdf VARCHAR(8) DEFAULT 'False',
    has_book VARCHAR(8) DEFAULT 'False',
    has_suppl VARCHAR(8) DEFAULT 'False',
    cited_by_count INTEGER DEFAULT 0,
    has_references VARCHAR(8) DEFAULT 'False',
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

