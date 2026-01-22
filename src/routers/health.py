from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.config.engine import engine

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/db")
def database_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    except SQLAlchemyError as exc:
        return {"status": "error", "database": "unreachable", "detail": str(exc)}
