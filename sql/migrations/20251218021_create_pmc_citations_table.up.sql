CREATE TABLE IF NOT EXISTS citations (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    ingestion_id INTEGER,
    citation_id VARCHAR(128),
    source VARCHAR(64),
    citation_type VARCHAR(500),
    title TEXT,
    authors TEXT,
    pub_year INTEGER,
    citation_count INTEGER DEFAULT 0,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(64),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_citations_article
      FOREIGN KEY (article_id)
      REFERENCES pmc_articles (id)
      ON DELETE CASCADE,
    CONSTRAINT fk_citations_ingestion
      FOREIGN KEY (ingestion_id)
      REFERENCES ingestion (id)
      ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_citations_article_id ON citations(article_id);
CREATE INDEX IF NOT EXISTS idx_citations_citation_id ON citations(citation_id);
CREATE INDEX IF NOT EXISTS idx_citations_citation_count ON citations(citation_count);
CREATE INDEX IF NOT EXISTS idx_citations_pub_year ON citations(pub_year);