# main.py
# import imp
import os
import time
import logging
import uvicorn
from fastapi import FastAPI

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from urllib.parse import quote
from sqlalchemy.orm import sessionmaker, Session

# config
from .config.constants import GH_BASE_URL
from src.config.session import get_session, SessionLocal
from src.config.engine import engine

# clients / repos / services / routers
from .clients.github import GithubRepoClient
from .repositories.github import GithubRepo as GithubRepoRepository
from .repositories import setup
from .services.github import GithubRepos as GithubReposService
from .routers.github import GithubRepoRouter
from .models.github import GithubRepo

from src.repositories.record import Record as RecordRepo

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
from .repositories import setup, sqlbuilder
from .routers.pypi import Pypi as PypiRouter
from .services.pypi import Pypi as PypiService
from .repositories.pypi import Pypi as PypiRepo
from .models.pypi import Pypi as PypiModel

from .clients import pubmed
from .config import constants
from .config.config import config
from .models.article import Article
from .models.author import Author
from .models.record import Record
from .repositories import setup, sqlbuilder
from .repositories.article import Article as ArticleRepo
from .repositories.author import Author as AuthorRepo
from .repositories.record import Record as RecordRepo
from .routers.pubmed import Pubmed as PubmedRouter
from .services.pubmed import Pubmed as PubmedService

from .routers.health import router as health_router
from .routers.epmc import EPMC as EPMCRouter

from contextlib import asynccontextmanager

from src.repositories.epmc import EPMCRepo
from src.services.epmc import EPMCService
from src.clients.epmc import EPMCClient
from src.services.grant import GrantService as Grant


def main() -> FastAPI:
    app = FastAPI()

    # DB setup
    try:
        sa_url = make_url(config.database_url)
        user = quote(sa_url.username or "", safe="")
        pwd = quote(sa_url.password or "", safe="")
        host = sa_url.host or ""
        port = sa_url.port or ""
        dbname = sa_url.database or ""
        dsn = f"postgresql://{user}:{pwd}@{host}:{port}/{dbname}"
    except Exception:
        # Fallback: pass the original URL through (may work if already libpq-compatible)
        dsn = config.database_url

    db_conn = setup.DatabaseConnection(dsn)
    db_conn.connect()
    session = SessionLocal()
    logger.info("Database connected via SQLAlchemy ORM")                     

    # Fields setup
    record_fields = set(Record.model_fields.keys())
    record_sql_builder = sqlbuilder.SQLBuilder("records").allow_fields(record_fields - {"id"})
    record_repo = RecordRepo(db_conn, record_sql_builder)

    article_fields = set(Article.model_fields.keys())
    article_sql_builder = sqlbuilder.SQLBuilder("articles").allow_fields(article_fields - {"id"})
    article_repo = ArticleRepo(db_conn, article_sql_builder)

    author_fields = set(Author.model_fields.keys())
    author_sql_builder = sqlbuilder.SQLBuilder("authors").allow_fields(author_fields - {"id"})
    author_repo = AuthorRepo(db_conn, author_sql_builder)

    # PubMed setup
    pubmed_client = pubmed.Pubmed(constants.PUBMED_BASE_URL, config.pubmed_api_key)
    pubmed_service = PubmedService(author_repo, record_repo, article_repo, pubmed_client)
    pubmed_router = PubmedRouter(pubmed_service)

    # GitHub setup
    gh_api_key = os.getenv("GITHUB_API_KEY", "")
    gh_org = os.getenv("GITHUB_ORG", "ga4gh")  # change via env if needed
    gh_client = GithubRepoClient(GH_BASE_URL, gh_api_key)
    gh_repo_fields = set(GithubRepo.model_fields.keys())
    gh_repo_sql_builder = sqlbuilder.SQLBuilder("github_repos").allow_fields(gh_repo_fields - {"id"})
    gh_repo = GithubRepoRepository(db_conn, gh_repo_sql_builder)
    gh_service = GithubReposService(gh_repo, gh_client, record_repo)
    gh_router = GithubRepoRouter(gh_service)

    # PyPi setup
    pypi_fields = set(PypiModel.model_fields.keys())
    pypi_sql_builder = sqlbuilder.SQLBuilder("pypi").allow_fields(pypi_fields)
    pypi_repo = PypiRepo(db_conn, pypi_sql_builder)
    pypi_service = PypiService(pypi_repo)
    pypi_router = PypiRouter(pypi_service)

    # EPMC setup
    epmc_repo = EPMCRepo(session)
    epmc_service = EPMCService(epmc_repo)
    epmc_router = EPMCRouter(epmc_service, session)

    # --- FastAPI app + router
    app.include_router(gh_router.router)
    app.include_router(pypi_router.router)
    app.include_router(pubmed_router.router)
    app.include_router(epmc_router.router)
    app.include_router(health_router)

    return app


if __name__ == "__main__":
    app = main()
    uvicorn.run(app, host=config.host, port=config.port, reload=False)