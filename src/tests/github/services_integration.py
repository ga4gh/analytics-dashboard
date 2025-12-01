import pytest
from datetime import datetime, timezone

import src.services.github as services_module


# ----------------------------
# In-memory integration doubles (simulate persistence + client)
# ----------------------------
class InMemoryRepo:
    """Minimal in-memory implementation of the GithubRepo repository interface."""
    def __init__(self):
        self._store = {}
        self._by_name = {}
        self._next_id = 1
        self.last_update_id = None
        self.last_update_updates = None

    def insert(self, model):
        model.id = self._next_id
        self._next_id += 1
        self._store[model.id] = model
        self._by_name.setdefault(model.name, []).append(model)
        return model.id

    def update(self, repo_id: int, updates: dict):
        self.last_update_id = repo_id
        self.last_update_updates = dict(updates)
        if repo_id in self._store:
            for k, v in updates.items():
                setattr(self._store[repo_id], k, v)

    def get_by_id(self, repo_id: int):
        return self._store.get(repo_id)

    def get_by_name(self, name: str):
        return list(self._by_name.get(name, []))


class InMemoryRecordRepo:
    def __init__(self, start_id=100):
        self._next = start_id
        self.created = []

    def create_record(self, record_model):
        self.created.append(record_model)
        rid = self._next
        self._next += 1
        return rid


class InMemoryRepoClient:
    def __init__(self):
        self.org_data = []
        self.single_repo = None
        self.branches = {}
        self.raise_branches = set()
        self.calls = {"get_repos_by_org": [], "get_repo_branches": [], "get_single_repo": 0}

    def get_repos_by_org(self, org: str):
        self.calls["get_repos_by_org"].append(org)
        return list(self.org_data)

    def get_single_repo(self):
        self.calls["get_single_repo"] += 1
        return dict(self.single_repo) if self.single_repo else None

    def get_repo_branches(self, owner: str, repo: str) -> int:
        self.calls["get_repo_branches"].append((owner, repo))
        if (owner, repo) in self.raise_branches:
            raise RuntimeError("branches error")
        return self.branches.get((owner, repo), 0)


# ----------------------------
# Dummy model + enums (so we don't need the real Pydantic models)
# ----------------------------
class DummyModel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def model_dump(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class DummyEnumBag:
    def __init__(self, **entries):
        for k, v in entries.items():
            setattr(self, k, v)


@pytest.fixture(autouse=True)
def patch_models(monkeypatch):
    # Replace models and enums in the service module namespace
    monkeypatch.setattr(services_module, "GithubRepoModel", DummyModel, raising=True)
    monkeypatch.setattr(services_module, "GithubRepoRequest", DummyModel, raising=True)

    monkeypatch.setattr(services_module, "RecordModel", DummyModel, raising=True)
    monkeypatch.setattr(services_module, "RecordType", DummyEnumBag(REPO="REPO"), raising=True)
    monkeypatch.setattr(services_module, "Source", DummyEnumBag(GITHUB="GITHUB"), raising=True)
    monkeypatch.setattr(services_module, "Status", DummyEnumBag(PENDING="PENDING"), raising=True)
    monkeypatch.setattr(services_module, "ProductType", DummyEnumBag(REFERENCE="REFERENCE"), raising=True)


# ----------------------------
# Integration-style tests (service wired to working in-memory repos + client)
# ----------------------------
@pytest.mark.integration
def test_create_then_update_and_fetch_flow():
    gh_repo = InMemoryRepo()
    record_repo = InMemoryRecordRepo(start_id=500)
    client = InMemoryRepoClient()
    svc = services_module.GithubRepos(gh_repo, client, record_repo)

    # Create via service
    req = DummyModel(
        name="svc-repo",
        repo_link="https://example/repo",
        owner="ga4gh",
        description="first",
        is_fork=False,
        last_updated=datetime(2024, 1, 1, tzinfo=timezone.utc),
        pushed_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        is_archived=False,
        license="Apache-2.0",
        stargazers_count=0,
        watchers_count=0,
        forks_count=0,
        open_issues_count=0,
        network_count=0,
        subscribers_count=0,
        branches_count=1,
    )
    created = svc.create_repo(req, user="alice")
    assert created.id == 1
    assert created.record_id == 500

    # Update
    out = svc.update_repo(1, {"description": "updated"}, user="alice")
    assert out.description == "updated"
    assert gh_repo.last_update_id == 1
    assert "updated_by" in gh_repo.last_update_updates
    assert "updated_at" in gh_repo.last_update_updates

    # Fetch by id + name
    assert svc.get_repo_by_id(1).name == "svc-repo"
    assert svc.get_repo_by_name("svc-repo")[0].id == 1


@pytest.mark.integration
def test_sync_from_json_creates_new_and_skips_existing_with_branch_fallback():
    gh_repo = InMemoryRepo()
    record_repo = InMemoryRecordRepo(start_id=700)
    client = InMemoryRepoClient()
    svc = services_module.GithubRepos(gh_repo, client, record_repo)

    # Seed existing name
    existing_req = DummyModel(
        name="exists",
        repo_link="",
        owner="o",
        description="",
        is_fork=False,
        last_updated=datetime.now(timezone.utc),
        pushed_at=datetime.now(timezone.utc),
        is_archived=False,
        license=None,
        stargazers_count=0,
        watchers_count=0,
        forks_count=0,
        open_issues_count=0,
        network_count=0,
        subscribers_count=0,
        branches_count=0,
    )
    svc.create_repo(existing_req, "seed")

    # Incoming data: one existing (skip), one new (create)
    repos_data = [
        {
            "name": "exists",
            "owner": {"login": "ga4gh"},
            "html_url": "https://github.com/ga4gh/exists",
            "description": "old",
            "fork": True,
            "updated_at": "2024-01-01T00:00:00Z",
            "pushed_at": "2024-01-02T00:00:00Z",
            "archived": False,
            "license": {"name": "MIT"},
            "stargazers_count": 1,
            "watchers_count": 2,
            "forks_count": 3,
            "open_issues_count": 4,
            "network_count": 0,
            "subscribers_count": 5,
        },
        {
            "name": "new-one",
            "owner": {"login": "ga4gh"},
            "html_url": "https://github.com/ga4gh/new-one",
            "description": "new",
            "fork": False,
            "updated_at": "2024-02-01T10:00:00Z",
            "pushed_at": "2024-02-02T10:00:00Z",
            "archived": True,
            "license": {"name": "Apache-2.0"},
            "stargazers_count": 10,
            "watchers_count": 20,
            "forks_count": 30,
            "open_issues_count": 40,
            "network_count": 0,
            "subscribers_count": 50,
        },
    ]

    # Make branch lookup fail for fallback=0
    client.raise_branches.add(("ga4gh", "new-one"))

    created = svc.sync_from_json(repos_data, user="u1")
    assert len(created) == 1
    assert created[0].name == "new-one"
    assert created[0].branches_count == 0
    assert created[0].license == "Apache-2.0"
    assert created[0].network_count == 30  # fallback to forks_count


@pytest.mark.integration
def test_sync_repos_and_sync_single_repo_paths():
    gh_repo = InMemoryRepo()
    record_repo = InMemoryRecordRepo(start_id=900)
    client = InMemoryRepoClient()
    svc = services_module.GithubRepos(gh_repo, client, record_repo)

    # Prepare org repos (both new)
    client.org_data = [
        {
            "name": "r1",
            "owner": {"login": "ga4gh"},
            "html_url": "https://github.com/ga4gh/r1",
            "description": "d1",
            "fork": False,
            "updated_at": "2024-01-01T00:00:00Z",
            "pushed_at": "2024-01-02T00:00:00Z",
            "archived": False,
            "license": None,
            "stargazers_count": 0,
            "watchers_count": 0,
            "forks_count": 0,
            "open_issues_count": 0,
            "network_count": 0,
            "subscribers_count": 0,
        },
        {
            "name": "r2",
            "owner": {"login": "ga4gh"},
            "html_url": "https://github.com/ga4gh/r2",
            "description": "d2",
            "fork": True,
            "updated_at": "2024-01-03T00:00:00Z",
            "pushed_at": "2024-01-04T00:00:00Z",
            "archived": False,
            "license": {"name": "MIT"},
            "stargazers_count": 1,
            "watchers_count": 2,
            "forks_count": 3,
            "open_issues_count": 4,
            "network_count": 5,
            "subscribers_count": 6,
        },
    ]
    client.branches[("ga4gh", "r1")] = 2
    client.branches[("ga4gh", "r2")] = 3

    synced = svc.sync_repos(user="sam", org="GA4GH")
    assert {r.name for r in synced} == {"r1", "r2"}
    assert client.calls["get_repos_by_org"] == ["GA4GH"]
    assert set(client.calls["get_repo_branches"]) == {("ga4gh", "r1"), ("ga4gh", "r2")}

    # Prepare single repo update path
    client.single_repo = {
        "name": "r1",
        "owner": {"login": "ga4gh"},
        "html_url": "https://github.com/ga4gh/r1",
        "description": "newdesc",
        "fork": False,
        "updated_at": "2024-05-01T00:00:00Z",
        "pushed_at": "2024-05-02T00:00:00Z",
        "archived": False,
        "license": {"name": "Apache-2.0"},
        "stargazers_count": 0,
        "watchers_count": 0,
        "forks_count": 0,
        "open_issues_count": 0,
        "network_count": 0,
        "subscribers_count": 0,
    }
    client.branches[("ga4gh", "r1")] = 4

    updated = svc.sync_single_repo(user="any")
    assert updated.name == "r1"
    assert updated.description == "newdesc"
    assert updated.branches_count == 4

    # Prepare single repo create path (new name)
    client.single_repo = {
        "name": "r3",
        "owner": {"login": "ga4gh"},
        "html_url": "https://github.com/ga4gh/r3",
        "description": "",
        "fork": True,
        "updated_at": "2024-06-01T00:00:00Z",
        "pushed_at": "2024-06-02T00:00:00Z",
        "archived": True,
        "license": None,
        "stargazers_count": 0,
        "watchers_count": 0,
        "forks_count": 0,
        "open_issues_count": 0,
        "network_count": 0,
        "subscribers_count": 0,
    }
    client.branches[("ga4gh", "r3")] = 1

    created = svc.sync_single_repo(user="creator")
    assert created.name == "r3"
    assert created.is_fork is True
    assert created.is_archived is True