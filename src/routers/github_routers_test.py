import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

import src.routers.github as router_module


# ----------------------------
# Dummy Pydantic models to patch into the router module
# ----------------------------
class DummyGithubRepo(BaseModel):
    id: int
    name: str
    owner: str
    description: str | None = None


class DummyGithubRepoRequest(BaseModel):
    name: str
    owner: str
    repo_link: str | None = None
    description: str | None = None


# ----------------------------
# Fake service to inject into the router
# ----------------------------
class FakeGithubRepoService:
    def __init__(self):
        self.calls = []

        # Return values configured by tests
        self.get_repo_by_id_return = None
        self.get_repo_by_name_return = []
        self.get_repos_by_owner_return = []
        self.create_repo_return = None
        self.update_repo_return = None

    # Service API expected by the router
    def get_repo_by_id(self, repo_id: int):
        self.calls.append(("get_repo_by_id", repo_id))
        return self.get_repo_by_id_return

    def get_repo_by_name(self, name: str):
        self.calls.append(("get_repo_by_name", name))
        return self.get_repo_by_name_return

    def get_repos_by_owner(self, owner: str):
        self.calls.append(("get_repos_by_owner", owner))
        return self.get_repos_by_owner_return

    def create_repo(self, repo_req, user: str):
        self.calls.append(("create_repo", repo_req, user))
        return self.create_repo_return

    def update_repo(self, repo_id: int, updates: dict, user: str):
        self.calls.append(("update_repo", repo_id, updates, user))
        return self.update_repo_return


@pytest.fixture
def app_client(monkeypatch):
    # Patch the models the router uses before instantiating the router
    monkeypatch.setattr(router_module, "GithubRepo", DummyGithubRepo, raising=True)
    monkeypatch.setattr(router_module, "GithubRepoRequest", DummyGithubRepoRequest, raising=True)

    service = FakeGithubRepoService()
    router_instance = router_module.GithubRepoRouter(service)

    app = FastAPI()
    app.include_router(router_instance.router)
    client = TestClient(app)
    return service, client


# ----------------------------
# Unit tests: verify behavior and service interactions
# ----------------------------
def test_get_repo_success(app_client):
    service, client = app_client
    service.get_repo_by_id_return = DummyGithubRepo(id=1, name="r1", owner="ga4gh", description="d")

    resp = client.get("/github/1")
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "name": "r1", "owner": "ga4gh", "description": "d"}
    assert ("get_repo_by_id", 1) in service.calls


def test_get_repo_not_found(app_client):
    service, client = app_client
    service.get_repo_by_id_return = None

    resp = client.get("/github/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Repo not found"
    assert ("get_repo_by_id", 999) in service.calls


def test_get_repo_by_name_success(app_client):
    service, client = app_client
    service.get_repo_by_name_return = [
        DummyGithubRepo(id=2, name="r2", owner="ga4gh", description=None)
    ]

    resp = client.get("/github/name/r2")
    assert resp.status_code == 200
    assert resp.json() == [{"id": 2, "name": "r2", "owner": "ga4gh", "description": None}]
    assert ("get_repo_by_name", "r2") in service.calls


def test_get_repo_by_name_404(app_client):
    service, client = app_client
    service.get_repo_by_name_return = []

    resp = client.get("/github/name/none")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "No repo found with that name"
    assert ("get_repo_by_name", "none") in service.calls


def test_get_repos_by_owner_success(app_client):
    service, client = app_client
    service.get_repos_by_owner_return = [
        DummyGithubRepo(id=1, name="r1", owner="ga4gh", description=None),
        DummyGithubRepo(id=2, name="r2", owner="ga4gh", description=None),
    ]

    resp = client.get("/github/owner/ga4gh")
    assert resp.status_code == 200
    assert resp.json() == [
        {"id": 1, "name": "r1", "owner": "ga4gh", "description": None},
        {"id": 2, "name": "r2", "owner": "ga4gh", "description": None},
    ]
    assert ("get_repos_by_owner", "ga4gh") in service.calls


def test_get_repos_by_owner_404(app_client):
    service, client = app_client
    service.get_repos_by_owner_return = []

    resp = client.get("/github/owner/ghost")
    assert resp.status_code == 404
    # Note: message reuses "name" text even for owner, as in the router code
    assert resp.json()["detail"] == "No repo found with that name"
    assert ("get_repos_by_owner", "ghost") in service.calls


def test_create_repo_calls_service_and_returns_200(app_client):
    service, client = app_client

    payload = {
        "name": "newrepo",
        "owner": "ga4gh",
        "repo_link": "https://github.com/ga4gh/newrepo",
        "description": "desc",
    }
    headers = {"user": "alice"}

    resp = client.post("/github", json=payload, headers=headers)
    assert resp.status_code == 200

    # Verify service call captured with correct args
    call = next(c for c in service.calls if c[0] == "create_repo")
    _, repo_req, user = call
    assert user == "alice"
    # repo_req is a DummyGithubRepoRequest instance
    assert repo_req.name == payload["name"]
    assert repo_req.owner == payload["owner"]
    assert repo_req.repo_link == payload["repo_link"]
    assert repo_req.description == payload["description"]


def test_create_repo_missing_user_header_returns_422(app_client):
    _, client = app_client
    payload = {"name": "n", "owner": "o"}
    resp = client.post("/github", json=payload)
    assert resp.status_code == 422  # missing required header


def test_update_repo_success(app_client):
    service, client = app_client
    updated = DummyGithubRepo(id=10, name="r", owner="o", description="new")
    service.update_repo_return = updated

    headers = {"user": "bob"}
    updates = {"description": "new"}

    resp = client.put("/github/10", json=updates, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"id": 10, "name": "r", "owner": "o", "description": "new"}

    call = next(c for c in service.calls if c[0] == "update_repo")
    _, repo_id, sent_updates, user = call
    assert repo_id == 10
    assert sent_updates == updates
    assert user == "bob"


def test_update_repo_not_found_returns_404(app_client):
    service, client = app_client
    service.update_repo_return = None

    resp = client.put("/github/404", json={"description": "x"}, headers={"user": "bob"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Repo not found"


def test_update_repo_missing_user_header_returns_422(app_client):
    _, client = app_client
    resp = client.put("/github/1", json={"description": "x"})
    assert resp.status_code == 422  # missing required header