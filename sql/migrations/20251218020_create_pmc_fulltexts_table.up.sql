CREATE TABLE IF NOT EXISTS fulltexts (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    ingestion_id INTEGER NOT NULL,
    availability VARCHAR(64),
    availability_code VARCHAR(32),
    document_style VARCHAR(32),
    site VARCHAR(64),
    url TEXT,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(64),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_fulltexts_article
      FOREIGN KEY (article_id)
      REFERENCES pmc_articles (id)
      ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fulltexts_article_id ON fulltexts(article_id);
