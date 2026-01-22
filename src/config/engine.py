from sqlalchemy import create_engine
from src.config.database import db_settings


engine = create_engine(
    db_settings.sqlalchemy_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)