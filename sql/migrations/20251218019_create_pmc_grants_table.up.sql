CREATE TABLE IF NOT EXISTS grants (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    grant_id VARCHAR(128),
    agency TEXT,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(64),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_grants_article
      FOREIGN KEY (article_id)
      REFERENCES pmc_articles (id)
      ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_grants_article_id ON grants(article_id);
CREATE INDEX IF NOT EXISTS idx_grants_grant_id ON grants(grant_id);