CREATE TABLE IF NOT EXISTS pmc_references (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    reference_id VARCHAR(128),
    source VARCHAR(64),
    citation_type VARCHAR(64),
    title TEXT,
    authors TEXT,
    pub_year INTEGER,
    issn VARCHAR(32),
    essn VARCHAR(32),
    cited_order INTEGER,
    match BOOLEAN,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(64),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_references_article
      FOREIGN KEY (article_id)
      REFERENCES pmc_articles (id)
      ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_references_article_id ON pmc_references(article_id);
CREATE INDEX IF NOT EXISTS idx_references_pub_year ON pmc_references(pub_year);
