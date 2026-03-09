CREATE TABLE IF NOT EXISTS articles_authors (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    ingestion_id INTEGER NOT NULL,
    author_order INTEGER,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by VARCHAR(64),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_by VARCHAR(64),
    deleted_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_articles_authors_article
      FOREIGN KEY (article_id)
      REFERENCES pmc_articles (id)
      ON DELETE CASCADE,
    CONSTRAINT fk_articles_authors_author
      FOREIGN KEY (author_id)
      REFERENCES authors (id)
      ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_articles_authors_article_id ON articles_authors(article_id);
CREATE INDEX IF NOT EXISTS idx_articles_authors_author_id ON articles_authors(author_id);
-- Unique constraint to prevent duplicate author entries for the same article/order
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_article_author_order ON articles_authors(article_id, author_id, author_order);
