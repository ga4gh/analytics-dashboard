CREATE TABLE IF NOT EXISTS pmc_keywords (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL
    values TEXT[],
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_keywords_article
      FOREIGN KEY (article_id)
      REFERENCES pmc_articles (id)
      ON DELETE CASCADE,
);

CREATE INDEX IF NOT EXISTS idx_pmc_keywords_article_id ON pmc_keywords(article_id);
