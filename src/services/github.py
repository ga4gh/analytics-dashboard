import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.models import record
from src.repositories.github import (
    GithubRepo as GhRepo,
    GithubEntities as GhEntitiesRepo,
    GithubEntityActions as GhEntityActionsRepo,
    GithubArchivedStats as GhArchivedStatsRepo,
)
from src.repositories.record import Record as RecordRepo
from src.models.github import (
    GithubRepo as GithubRepoModel,
    GithubRepoRequest,
    GithubEntity as GithubEntityModel,
    GithubEntityRequest,
    GithubEntityAction as GithubEntityActionModel,
    GithubEntityActionRequest,
    GithubArchivedStat as GithubArchivedStatModel,
    GithubArchivedStatRequest,
)
from src.models.record import (
    Record as RecordModel,
    RecordType,
    Source,
    Status,
    ProductType,
)
from src.clients.github import (
    GithubRepoClient,
    GithubEntityClient,
    GithubEntityActionsClient,
    GithubArchivedStatsClient,
)

import uuid

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GithubRepos:
    def __init__(
        self, 
        repo: GhRepo, 
        repo_client: GithubRepoClient, 
        record_repo: RecordRepo
    ) -> None:
        self.github_repo = repo
        self.repo_client = repo_client
        self.record_repo = record_repo

    def get_repo_by_id(self, repo_id: int) -> Optional[GithubRepoModel]:
        return self.github_repo.get_by_id(repo_id)

    def get_repo_by_name(self, name: str) -> List[GithubRepoModel]:
        return self.github_repo.get_by_name(name)

    def create_repo(self, repo_request: GithubRepoRequest, user: str) -> GithubRepoModel:
        
        record_model = RecordModel(
            record_type=RecordType.REPO,
            source=Source.GITHUB,
            status=Status.PENDING,          
            keyword=[repo_request.name],
            product_line=ProductType.REFERENCE,
            created_at=datetime.now(),
            created_by=user,
            updated_at=datetime.now(),
            updated_by=user,
            deleted_at=None,
            deleted_by=None,
            version=1
        )

        try:
            record_id = self.record_repo.create_record(record_model)
            logger.info(f"Created record id {record_id} for repo {repo_request.name}")
        except Exception as e:
            logger.exception("Failed to create record for repo; aborting repo creation.")
            raise

        complete_repo_model = GithubRepoModel(
            record_id=record_id,
            name=repo_request.name,
            repo_link=repo_request.repo_link,            
            owner=repo_request.owner,
            description=repo_request.description,
            is_fork=repo_request.is_fork,
            last_updated=repo_request.last_updated,
            pushed_at=repo_request.pushed_at,
            is_archived=repo_request.is_archived,
            license=repo_request.license,
            stargazers_count=repo_request.stargazers_count,
            watchers_count=repo_request.watchers_count,
            forks_count=repo_request.forks_count,
            open_issues_count=repo_request.open_issues_count,
            network_count=repo_request.network_count,
            subscribers_count=repo_request.subscribers_count,
            branches_count=repo_request.branches_count,
            created_at=datetime.now(),
            created_by=user,
            updated_at=datetime.now(),
            updated_by=user,
            version=1,
        )
        self.github_repo.insert(complete_repo_model)
        return complete_repo_model

    def update_repo(self, repo_id: int, updates: Dict[str, Any], user: str) -> Optional[GithubRepoModel]:
        """
        Update DB row for repo_id with updates mapping (keys should be DB column names
        that correspond to model_dump keys).
        Returns the updated model (re-query) or None if not found.
        """
        existing = self.github_repo.get_by_id(repo_id)
        if not existing:
            return None

        # add updated_by/updated_at if present in model schema
        updates.setdefault("updated_at", datetime.now())
        updates.setdefault("updated_by", user)

        self.github_repo.update(repo_id, updates)
        return self.github_repo.get_by_id(repo_id)

    def sync_repos(self, user: str, org: str) -> List[GithubRepoModel]:
        repos_data = self.repo_client.get_repos_by_org(org)
        return self.sync_from_json(repos_data, user)

    def sync_from_json(self, repos_data: List[Dict[str, Any]], user: str) -> List[GithubRepoModel]:
        """
        Process a list of repo JSON objects (e.g. loaded from GitHub API or local file).
        This will skip existing repos (by name) and insert new ones.
        """
        synced_repos = []
        for repo in repos_data:
            existing = self.github_repo.get_by_name(repo["name"])
            if existing:
                logger.info(f"Repo {repo['name']} already exists, skipping.")
                continue

            try:
                branch_count = self.repo_client.get_repo_branches(repo["owner"]["login"], repo["name"])
            except Exception:
                logger.warning(f"Could not fetch branches for {repo['name']}; defaulting to 0.")
                branch_count = 0

            # convert timestamps
            def to_dt(s: str) -> datetime:
                if not s:
                    return datetime.now()
                try:
                    return datetime.fromisoformat(s.replace("Z", "+00:00"))
                except Exception:
                    return datetime.now()

            repo_request = GithubRepoRequest(
                name=repo["name"],
                repo_link=repo.get("html_url", ""),
                owner=repo["owner"]["login"],
                description=repo.get("description", ""),
                is_fork=repo.get("fork", False),
                last_updated=to_dt(repo.get("updated_at")),
                pushed_at=to_dt(repo.get("pushed_at")),
                is_archived=repo.get("archived", False),
                license=(repo.get("license") or {}).get("name") if repo.get("license") else None,
                stargazers_count=repo.get("stargazers_count", 0),
                watchers_count=repo.get("watchers_count", 0),
                forks_count=repo.get("forks_count", 0),
                open_issues_count=repo.get("open_issues_count", 0),
                network_count=repo.get("network_count", 0) or repo.get("forks_count", 0),
                subscribers_count=repo.get("subscribers_count", 0),
                branches_count=branch_count,
            )
            created = self.create_repo(repo_request, user)
            logger.info(f"Repo {created.name} synced successfully.")
            synced_repos.append(created)
        return synced_repos

    def sync_single_repo(self, user: str) -> GithubRepoModel:
        repo = self.repo_client.get_single_repo()
        try:
            branch_count = self.repo_client.get_repo_branches(repo["owner"]["login"], repo["name"])
        except Exception:
            branch_count = 0

        existing = self.github_repo.get_by_name(repo["name"])
        repo_request = GithubRepoRequest(
            name=repo["name"],
            repo_link=repo.get("html_url", ""),
            owner=repo["owner"]["login"],
            description=repo.get("description", ""),
            is_fork=repo.get("fork", False),
            last_updated=datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00")),
            pushed_at=datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00")),
            is_archived=repo.get("archived", False),
            license=(repo.get("license") or {}).get("name") if repo.get("license") else None,
            stargazers_count=repo.get("stargazers_count", 0),
            watchers_count=repo.get("watchers_count", 0),
            forks_count=repo.get("forks_count", 0),
            open_issues_count=repo.get("open_issues_count", 0),
            network_count=repo.get("network_count", 0),
            subscribers_count=repo.get("subscribers_count", 0),
            branches_count=branch_count,
        )

        if existing:
            logger.info(f"Updating existing repo {repo['name']}")
            # update existing DB row (use DB column names that match model_dump)
            updates = repo_request.model_dump()
            # remove fields that should not be updated or that are created_by etc
            updates.pop("created_at", None)
            updates.pop("created_by", None)
            # find DB id:
            db_id = existing[0].id
            self.github_repo.update(db_id, updates)
            return self.github_repo.get_by_id(db_id)
        else:
            logger.info(f"Creating new repo {repo['name']}")
            created = self.create_repo(repo_request, user)
            return created
