import logging
from datetime import datetime
from typing import List, Optional
from src.repositories.github import (
    GithubRepo as GhRepo,
    GithubEntities as GhEntitiesRepo,
    GithubEntityActions as GhEntityActionsRepo,
    GithubArchievedStats as GhArchievedStatsRepo,
)
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
from src.clients.github import (
    GithubRepoClient,
    GithubEntityClient,
    GithubEntityActionsClient,
    GithubArchivedStatsClient,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GithubRepos:
    def __init__(self, repo: GhRepo, repo_client: GithubRepoClient):
        self.github_repo = repo
        self.repo_client = repo_client

    def get_repo_by_id(self, repo_id: int) -> Optional[GithubRepoModel]:
        return self.github_repo.get_repo_by_id(repo_id)

    def get_repo_by_name(self, name: str) -> List[GithubRepoModel]:
        return self.github_repo.get_repo_by_name(name)

    def create_repo(self, repo_request: GithubRepoRequest, user: str) -> GithubRepoModel:
        complete_repo_model = GithubRepoModel(
            id=0,
            record_id="temp",
            name=repo_request.name,
            repo_link=repo_request.repo_link,
            owner=repo_request.owner,
            description=repo_request.description,
            fork=repo_request.fork,
            last_update=repo_request.last_update,
            pushed_at=repo_request.pushed_at,
            archived=repo_request.archived,
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
        self.github_repo.create_repo(complete_repo_model)
        return complete_repo_model

    def sync_repos(self, user: str) -> List[GithubRepoModel]:
        repos_data = self.repo_client.get_gh_repos()
        synced_repos = []

        for repo in repos_data:
            existing = self.github_repo.get_repo_by_name(repo["name"])
            if existing:
                logger.info(f"Repo {repo['name']} already exists, skipping.")
                continue

            try:
                branch_count = self.repo_client.get_repo_branches(repo["owner"]["login"], repo["name"])
            except Exception as e:
                logger.warning(f"Could not fetch branches for {repo['name']}: {e}")
                branch_count = 0

            repo_request = GithubRepoRequest(
                name=repo["name"],
                repo_link=repo["html_url"],
                owner=repo["owner"]["login"],
                description=repo.get("description", ""),
                fork=repo.get("fork", False),
                last_update=datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00")),
                pushed_at=datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00")),
                archived=repo.get("archived", False),
                license=repo["license"]["name"] if repo.get("license") else "Unknown",
                stargazers_count=repo.get("stargazers_count", 0),
                watchers_count=repo.get("watchers_count", 0),
                forks_count=repo.get("forks_count", 0),
                open_issues_count=repo.get("open_issues_count", 0),
                network_count=repo.get("network_count", 0),
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
        except Exception as e:
            logger.warning(f"Could not fetch branches for {repo['name']}: {e}")
            branch_count = 0

        existing = self.github_repo.get_repo_by_name(repo["name"])
        repo_request = GithubRepoRequest(
            name=repo["name"],
            repo_link=repo["html_url"],
            owner=repo["owner"]["login"],
            description=repo.get("description", ""),
            fork=repo.get("fork", False),
            last_update=datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00")),
            pushed_at=datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00")),
            archived=repo.get("archived", False),
            license=repo.get("license", {}).get("name") if repo.get("license") else None,
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
            updated = self.github_repo.update_repo(existing[0])
            return updated
        else:
            logger.info(f"Creating new repo {repo['name']}")
            created = self.create_repo(repo_request, user)
            return created


class GithubEntities:
    def __init__(self, repo: GhEntitiesRepo, client: GithubEntityClient):
        self.github_entity = repo
        self.entity_client = client

    def create_entity(self, entity_request: GithubEntityRequest, user: str) -> GithubEntityModel:
        complete_entity_model = GithubEntityModel(
            id=0,
            name=entity_request.name,
            user_id=entity_request.user_id,
            company=entity_request.company,
            email=entity_request.email,
            location=entity_request.location,
            type=entity_request.type,
            created_at=datetime.now(),
            created_by=user,
            updated_at=datetime.now(),
            updated_by=user,
            version=1,
        )
        self.github_entity.create_entity(complete_entity_model)
        return complete_entity_model

    def sync_entities(self, user: str) -> List[GithubEntityModel]:
        entities_data = self.entity_client.get_gh_repo_collaborators()
        synced_entities = []

        for entity in entities_data:
            existing = self.github_entity.get_entity_by_id(entity["id"])
            if existing:
                logger.info(f"Entity {entity['login']} already exists, skipping.")
                continue

            entity_request = GithubEntityRequest(
                name=entity["login"],
                user_id=str(entity["id"]),
                company=entity.get("company", ""),
                email=entity.get("email", ""),
                location=entity.get("location", ""),
                type=entity.get("type", "User"),
            )
            created = self.create_entity(entity_request, user)
            logger.info(f"Entity {created.name} synced successfully.")
            synced_entities.append(created)

        return synced_entities


class GithubEntityActions:
    def __init__(self, repo: GhEntityActionsRepo, client: GithubEntityActionsClient):
        self.github_entity_actions = repo
        self.actions_client = client

    def create_action(self, action_request: GithubEntityActionRequest, user: str) -> GithubEntityActionModel:
        complete_action_model = GithubEntityActionModel(
            id=0,
            repo_id=action_request.repo_id,
            action_type=action_request.action_type,
            user_id=action_request.user_id,
            created_at=datetime.now(),
            created_by=user,
            updated_at=datetime.now(),
            updated_by=user,
            version=1,
        )
        self.github_entity_actions.create_action(complete_action_model)
        return complete_action_model

    def sync_actions(self, repo_id: str, user: str) -> List[GithubEntityActionModel]:
        actions_data = self.actions_client.get_gh_repo_stargazers()
        synced_actions = []

        for action in actions_data:
            existing = self.github_entity_actions.get_action_by_user_and_repo(action["id"], repo_id)
            if existing:
                logger.info(f"Action for user {action['id']} on repo {repo_id} already exists, skipping.")
                continue

            action_request = GithubEntityActionRequest(
                repo_id=repo_id,
                action_type="stargazer",
                user_id=str(action["id"]),
            )
            created = self.create_action(action_request, user)
            logger.info(f"Action {created.user_id} synced for repo {repo_id}.")
            synced_actions.append(created)

        return synced_actions


class GithubArchivedStats:
    def __init__(self, repo: GharchivedStatsRepo, client: GithubArchivedStatsClient):
        self.github_archived_stats = repo
        self.stats_client = client

    def create_stats(self, stats_request: GithubArchivedStatRequest, user: str) -> GithubArchivedStatModel:
        complete_stats_model = GithubArchivedStatModel(
            id=0,
            repo_id=stats_request.repo_id,
            weekly_commit_add=stats_request.weekly_commit_add,
            weekly_commit_del=stats_request.weekly_commit_del,
            yearly_commit_count=stats_request.yearly_commit_count,
            daily_clone_count=stats_request.daily_clone_count,
            daily_view_count=stats_request.daily_view_count,
            last_14_day_top_referral_sources=stats_request.last_14_day_top_referral_sources,
            last_14_day_top_referral_path=stats_request.last_14_day_top_referral_path,
            created_at=datetime.now(),
            created_by=user,
            updated_at=datetime.now(),
            updated_by=user,
            version=1,
        )
        self.github_archived_stats.create_stats(complete_stats_model)
        return complete_stats_model

    def sync_stats(self, repo_id: str, user: str) -> GithubArchivedStatModel:
        existing = self.github_archived_stats.get_stats_by_repo(repo_id)
        if existing:
            logger.info(f"Stats for repo {repo_id} already exist, skipping.")
            return existing

        stats_data = {
            "weekly_commit_add": self.stats_client.get_gh_weekly_commit().get("additions", 0),
            "weekly_commit_del": self.stats_client.get_gh_weekly_commit().get("deletions", 0),
            "yearly_commit_count": self.stats_client.get_gh_yearly_commit_count(),
            "daily_clone_count": self.stats_client.get_gh_daily_clone_count().get("count", 0),
            "daily_view_count": self.stats_client.get_gh_daily_view_count().get("count", 0),
            "last_14_day_top_referral_sources": self.stats_client.get_gh_last_14_day_referral_source(),
            "last_14_day_top_referral_path": self.stats_client.get_gh_last_14_day_referral_path(),
        }

        stats_request = GithubArchivedStatRequest(
            repo_id=repo_id,
            weekly_commit_add=stats_data["weekly_commit_add"],
            weekly_commit_del=stats_data["weekly_commit_del"],
            yearly_commit_count=stats_data["yearly_commit_count"],
            daily_clone_count=stats_data["daily_clone_count"],
            daily_view_count=stats_data["daily_view_count"],
            last_14_day_top_referral_sources=stats_data["last_14_day_top_referral_sources"],
            last_14_day_top_referral_path=stats_data["last_14_day_top_referral_path"],
        )

        created = self.create_stats(stats_request, user)
        logger.info(f"Stats for repo {repo_id} synced successfully.")
        return created
