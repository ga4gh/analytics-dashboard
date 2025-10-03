# main.py
import os
import logging
import uvicorn
from fastapi import FastAPI

# config
from src.config.config import config
from src.config.constants import GH_BASE_URL

# clients / repos / services / routers
from src.clients.github import GithubRepoClient
from src.repositories.github import GithubRepo
from src.repositories import setup
from src.services.github import GithubRepos as GithubReposService
from src.routers.github import GithubRepoRouter

from src.repositories.record import Record as RecordRepo

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
    gh_org = os.getenv("GITHUB_ORG", "ga4gh")  # change via env if needed

    gh_client = GithubRepoClient(GH_BASE_URL, gh_api_key, gh_org)
    gh_repo = GithubRepo(db_conn, table_name="github_repos")
    print("record repo")
    record_repo = RecordRepo(db_conn, table_name="records")
    gh_service = GithubReposService(gh_repo, gh_client, record_repo)
    gh_router = GithubRepoRouter(gh_service)

    # Optionally sync repos once at startup
    # The service.sync_repos expects a `user` string (created_by/updated_by).
    sync_user = os.getenv("GITHUB_SYNC_USER", "system")
    try:
        logger.info("Starting GitHub repos sync...")
        synced = gh_service.sync_repos(sync_user)
        logger.info("GitHub sync completed. %d repos synced.", len(synced))
    except Exception as e:
        logger.exception("GitHub sync failed: %s", e)

    # --- FastAPI app + router
    app = FastAPI()
    app.include_router(gh_router.router)

    return app


if __name__ == "__main__":
    app = main()
    uvicorn.run(app, host=config.host, port=config.port, reload=config.debug)
