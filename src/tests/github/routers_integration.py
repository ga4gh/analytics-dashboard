import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict

import src.routers.github as router_module


# Use realistic Pydantic models for integration behavior (Pydantic v2 style config)
class GithubRepoModel(BaseModel):
    id: int
    name: str
    owner: str
    description: str | None = None

    # Pydantic v2 config
    model_config = ConfigDict(extra="ignore")


class GithubRepoRequestModel(BaseModel):
    name: str
    owner: str
    repo_link: str | None = None
    description: str | None = None

    # Pydantic v2 config (forbid unexpected fields on create, optional)
    model_config = ConfigDict(extra="forbid")


class InMemoryGithubService:
    """A simple in-memory service to emulate CRUD behaviors."""
    def __init__(self):
        self._data: dict[int, dict] = {}
        self._by_name: dict[str, list[int]] = {}
        self._by_owner: dict[str, list[int]] = {}
        self._next_id = 1

    def seed(self, name: str, owner: str, description: str | None = None):
        rid = self._next_id
        self._next_id += 1
        rec = {"id": rid, "name": name, "owner": owner, "description": description}
        self._data[rid] = rec
        self._by_name.setdefault(name, []).append(rid)
        self._by_owner.setdefault(owner, []).append(rid)
        return rec

    def get_repo_by_id(self, repo_id: int):
        rec = self._data.get(repo_id)
        return GithubRepoModel(**rec) if rec else None

    def get_repo_by_name(self, name: str):
        ids = self._by_name.get(name, [])
        return [GithubRepoModel(**self._data[i]) for i in ids]

    def get_repos_by_owner(self, owner: str):
        ids = self._by_owner.get(owner, [])
        return [GithubRepoModel(**self._data[i]) for i in ids]

    def create_repo(self, repo_req: GithubRepoRequestModel, user: str):
        # Simulate persistence on create
        rec = self.seed(name=repo_req.name, owner=repo_req.owner, description=repo_req.description)
        return GithubRepoModel(**rec)

    def update_repo(self, repo_id: int, updates: dict, user: str):
        if repo_id not in self._data:
            return None
        self._data[repo_id].update(updates)
        return GithubRepoModel(**self._data[repo_id])


@pytest.fixture
def app_client():
    # Patch models so response_model and request model validation run with our models
    router_module.GithubRepo = GithubRepoModel
    router_module.GithubRepoRequest = GithubRepoRequestModel

    service = InMemoryGithubService()
    # Seed some data
    service.seed("r1", "ga4gh", "first")
    service.seed("r2", "ga4gh", "second")

    router_instance = router_module.GithubRepoRouter(service)
    app = FastAPI()
    app.include_router(router_instance.router)
    client = TestClient(app)
    return service, client


# ----------------------------
# Integration tests: end-to-end HTTP behavior and validation
# ----------------------------
@pytest.mark.integration
def test_get_repo_and_validation(app_client):
    _, client = app_client

    # Valid id returns object
    resp = client.get("/github/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "r1"

    # Invalid path param type produces 422
    resp2 = client.get("/github/not-a-number")
    assert resp2.status_code == 422


@pytest.mark.integration
def test_get_by_name_and_owner_paths(app_client):
    _, client = app_client

    # By name existing
    resp = client.get("/github/name/r2")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert resp.json()[0]["name"] == "r2"

    # By name missing -> 404
    resp2 = client.get("/github/name/missing")
    assert resp2.status_code == 404
    assert resp2.json()["detail"] == "No repo found with that name"

    # By owner existing
    resp3 = client.get("/github/owner/ga4gh")
    assert resp3.status_code == 200
    assert {r["name"] for r in resp3.json()} == {"r1", "r2"}

    # By owner missing -> 404 (router uses same detail text)
    resp4 = client.get("/github/owner/ghost")
    assert resp4.status_code == 404
    assert resp4.json()["detail"] == "No repo found with that name"


@pytest.mark.integration
def test_create_repo_request_model_and_header_requirement(app_client):
    _, client = app_client

    # Missing required fields -> 422 from Pydantic
    resp_bad = client.post("/github", json={"owner": "ga4gh"}, headers={"user": "u"})
    assert resp_bad.status_code == 422

    # Missing required header -> 422
    resp_nohdr = client.post("/github", json={"name": "r3", "owner": "ga4gh"})
    assert resp_nohdr.status_code == 422

    # Valid create -> 200, then retrievable
    payload = {"name": "r3", "owner": "ga4gh", "repo_link": "https://example", "description": "third"}
    resp_ok = client.post("/github", json=payload, headers={"user": "alice"})
    assert resp_ok.status_code == 200

    # Ensure it was created by fetching by name
    by_name = client.get("/github/name/r3")
    assert by_name.status_code == 200
    assert by_name.json()[0]["description"] == "third"


@pytest.mark.integration
def test_update_repo_and_response_model_filtering(app_client):
    _, client = app_client

    # Update existing
    resp = client.put("/github/1", json={"description": "updated", "extra_field": "ignoreme"}, headers={"user": "bob"})
    assert resp.status_code == 200
    # Response model should filter out unknown fields (extra_field not present)
    body = resp.json()
    assert body["description"] == "updated"
    assert "extra_field" not in body

    # Update non-existent -> 404
    resp2 = client.put("/github/9999", json={"description": "x"}, headers={"user": "bob"})
    assert resp2.status_code == 404
    assert resp2.json()["detail"] == "Repo not found"

    # Missing header -> 422
    resp3 = client.put("/github/1", json={"description": "again"})
    assert resp3.status_code == 422
