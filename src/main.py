import logging
import os
from src.repositories import sqlbuilder

import uvicorn
from fastapi import FastAPI

# clients / repos / services / routers
from src.clients.github import GithubRepoClient
# config
from src.config.config import config
from src.config.constants import GH_BASE_URL
from src.repositories import setup
from src.repositories.github import GithubRepo
from src.repositories.record import Record as RecordRepo
from src.routers.github import GithubRepoRouter
from src.services.github import GithubRepos as GithubReposService
from src.repositories.sqlbuilder import SQLBuilder
from src.models.github import GithubRepo as GithubRepoModel
from src.models.record import Record as RecordModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main() -> FastAPI:
    # --- DB setup
    db_url = getattr(config, "database_url", None)
    if not db_url:
        raise RuntimeError("Database URL not configured in config.database_url")

    db_conn = setup.DatabaseConnection(db_url)
    db_conn.connect()
    logger.info("Database connected")

    # --- GitHub client + service setup
    gh_api_key = os.getenv("GITHUB_API_KEY", "")
    #gh_org = os.getenv("GITHUB_ORG", "ga4gh")  # change via env if needed

    gh_client = GithubRepoClient(GH_BASE_URL, gh_api_key)
    github_repo_fields = set(GithubRepoModel.model_fields.keys())
    gh_sql_builder = sqlbuilder.SQLBuilder("github_repos").allow_fields(github_repo_fields)
    gh_repo = GithubRepo(db_conn, gh_sql_builder)
    print("record repo")
    record_repo_fields = set(RecordModel.model_fields.keys())
    record_sql_builder = sqlbuilder.SQLBuilder("records").allow_fields(record_repo_fields)
    record_repo = RecordRepo(db_conn, record_sql_builder)


    gh_service = GithubReposService(gh_repo, record_repo, gh_client)
    gh_router = GithubRepoRouter(gh_service)

    # --- FastAPI app + router
    app = FastAPI()
    app.include_router(gh_router.router)

    return app


if __name__ == "__main__":
    app = main()
    uvicorn.run(app, host=config.host, port=config.port, reload=config.debug)