CREATE TABLE IF NOT EXISTS pmc_keywords (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    ingestion_id INTEGER,
    value TEXT[],
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(64),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_keywords_article
      FOREIGN KEY (article_id)
      REFERENCES pmc_articles (id)
      ON DELETE CASCADE,
    CONSTRAINT fk_keywords_ingestion
      FOREIGN KEY (ingestion_id)
      REFERENCES ingestion (id)
      ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pmc_keywords_article_id ON pmc_keywords(article_id);
CREATE INDEX IF NOT EXISTS idx_pmc_keywords_ingestion_id ON pmc_keywords(ingestion_id);
