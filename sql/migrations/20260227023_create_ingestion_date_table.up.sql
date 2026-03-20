CREATE TABLE IF NOT EXISTS ingestion (
    id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_ingested_at ON ingestion(ingested_at);
CREATE INDEX IF NOT EXISTS idx_ingestion_version ON ingestion(version);