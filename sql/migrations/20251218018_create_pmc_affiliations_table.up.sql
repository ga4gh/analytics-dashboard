CREATE TABLE IF NOT EXISTS pmc_affiliations (
    id SERIAL PRIMARY KEY,
    author_id INTEGER NOT NULL,
    ingestion_id INTEGER,
    org_name TEXT,
    article_id INTEGER NOT NULL,
    affiliation_order INTEGER NOT NULL,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(64),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_affiliations_author
      FOREIGN KEY (author_id)
      REFERENCES pmc_authors (id)
      ON DELETE CASCADE,
    CONSTRAINT fk_pmc_affiliations_article
      FOREIGN KEY (article_id)
      REFERENCES pmc_articles (id)
      ON DELETE CASCADE,
    CONSTRAINT fk_pmc_affiliations_ingestion
      FOREIGN KEY (ingestion_id)
      REFERENCES ingestion (id)
      ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_affiliations_author_id ON pmc_affiliations(author_id);
CREATE INDEX IF NOT EXISTS idx_affiliations_article_id ON pmc_affiliations(article_id);
CREATE INDEX IF NOT EXISTS idx_affiliations_org ON pmc_affiliations(org_name);