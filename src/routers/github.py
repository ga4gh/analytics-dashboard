from fastapi import APIRouter, Header, HTTPException, Response
from typing import List

from src.models.github import GithubRepo, GithubRepoRequest
from src.services.github import GithubRepos as GithubRepoService


class GithubRepoRouter:
    def __init__(self, github_service: GithubRepoService) -> None:
        self.router = APIRouter()
        self.github_service = github_service
        self._setup_routes()

    def _setup_routes(self) -> None:

        @self.router.get("/github/{repo_id}", response_model=GithubRepo)
        async def get_repo(repo_id: int) -> GithubRepo:
            repo = self.github_service.get_repo_by_id(repo_id)
            if repo is None:
                raise HTTPException(status_code=404, detail="Repo not found")
            return repo

        @self.router.get("/github/name/{name}", response_model=List[GithubRepo])
        async def get_repo_by_name(name: str) -> List[GithubRepo]:
            repo = self.github_service.get_repo_by_name(name)
            if not repo:
                raise HTTPException(status_code=404, detail="No repo found with that name")
            return repo

        @self.router.get("/github/owner/{owner}", response_model=List[GithubRepo])
        async def get_repos_by_owner(owner: str) -> List[GithubRepo]:
            repo = self.github_service.get_repos_by_owner(owner)
            if not repo:
                raise HTTPException(status_code=404, detail="No repo found with that name")
            return repo

        @self.router.post("/github")
        async def create_repo(repo: GithubRepoRequest, user: str = Header(...)) -> Response:
            self.github_service.create_repo(repo, user)
            return Response(status_code=200)

        @self.router.put("/github/{repo_id}", response_model=GithubRepo)
        async def update_repo(repo_id: int, updates: dict, user: str = Header(...)) -> GithubRepo | None:
            updated_repo = self.github_service.update_repo(repo_id, updates, user)
            if updated_repo is None:
                raise HTTPException(status_code=404, detail="Repo not found")
            return updated_repo
