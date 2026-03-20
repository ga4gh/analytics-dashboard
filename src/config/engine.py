from sqlalchemy import create_engine
from importlib import util
from src.config.database import db_settings


# Ensure the SQLAlchemy URL uses a DBAPI driver that is actually installed.
# If the configured URL doesn't specify a driver (e.g. starts with "postgresql://"),
# prefer the `psycopg` driver when available, otherwise fall back to `psycopg2`.
url = db_settings.sqlalchemy_url
if url.startswith("postgresql://"):
    if util.find_spec("psycopg"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif util.find_spec("psycopg2"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(
    url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)