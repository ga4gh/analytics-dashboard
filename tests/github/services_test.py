import pytest
from datetime import datetime, timezone

import src.services.github as services_module


# ----------------------------
# Test doubles and helpers
# ----------------------------
class DummyModel:
    """
    Generic dummy model used to replace Pydantic models in the services layer.
    Stores kwargs and returns them via model_dump.
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def model_dump(self):
        # Return only public-like attributes
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class DummyRequest(DummyModel):
    pass


class DummyRecordModel(DummyModel):
    pass


class DummyEnumBag:
    """Simple object to emulate enums with attributes used in the service."""
    def __init__(self, **entries):
        for k, v in entries.items():
            setattr(self, k, v)


class FakeGhRepo:
    def __init__(self):
        self.by_id = {}
        self.by_name = {}
        self.created_models = []
        self.last_update_id = None
        self.last_update_updates = None

    def insert(self, model):
        self.created_models.append(model)
        # Mimic DB assigning id and storing it
        new_id = len(self.by_id) + 1
        model.id = new_id
        self.by_id[new_id] = model
        self.by_name.setdefault(model.name, []).append(model)
        return new_id

    def update(self, repo_id: int, updates):
        self.last_update_id = repo_id
        self.last_update_updates = dict(updates)
        if repo_id in self.by_id:
            for k, v in updates.items():
                setattr(self.by_id[repo_id], k, v)

    def get_by_id(self, repo_id: int):
        return self.by_id.get(repo_id)

    def get_by_name(self, name: str):
        return self.by_name.get(name, [])


class FakeRecordRepo:
    def __init__(self, return_id=100, raise_exc=False):
        self.return_id = return_id
        self.raise_exc = raise_exc
        self.created = []

    def create_record(self, record_model):
        if self.raise_exc:
            raise RuntimeError("record create failed")
        self.created.append(record_model)
        return self.return_id


class FakeRepoClient:
    def __init__(self):
        self.repos = []
        self.single_repo = None
        self.branches_result = 0
        self.branches_raise = False
        self.call_log = {"get_repos_by_org": [], "get_repo_branches": [], "get_single_repo": 0}

    def get_repos_by_org(self, org: str):
        self.call_log["get_repos_by_org"].append(org)
        return list(self.repos)

    def get_single_repo(self):
        self.call_log["get_single_repo"] += 1
        return dict(self.single_repo) if self.single_repo else None

    def get_repo_branches(self, owner: str, repo: str) -> int:
        # Track calls for assertion
        self.call_log["get_repo_branches"].append((owner, repo))
        if self.branches_raise:
            raise RuntimeError("branches error")
        return self.branches_result


# ----------------------------
# Global model patches
# ----------------------------
@pytest.fixture(autouse=True)
def patch_models(monkeypatch):
    """
    Patch model classes and enums inside the services module so tests don't rely on
    real Pydantic/enums. This keeps tests hermetic.
    """
    # github models
    monkeypatch.setattr(services_module, "GithubRepoModel", DummyModel, raising=True)
    monkeypatch.setattr(services_module, "GithubRepoRequest", DummyRequest, raising=True)

    # record model and enums
    monkeypatch.setattr(services_module, "RecordModel", DummyRecordModel, raising=True)
    monkeypatch.setattr(
        services_module,
        "RecordType",
        DummyEnumBag(REPO="REPO"),
        raising=True,
    )
    monkeypatch.setattr(
        services_module,
        "Source",
        DummyEnumBag(GITHUB="GITHUB"),
        raising=True,
    )
    monkeypatch.setattr(
        services_module,
        "Status",
        DummyEnumBag(PENDING="PENDING"),
        raising=True,
    )
    monkeypatch.setattr(
        services_module,
        "ProductType",
        DummyEnumBag(REFERENCE="REFERENCE"),
        raising=True,
    )


# ----------------------------
# GithubRepos service unit tests
# ----------------------------
def test_get_repo_by_id_and_name_passthrough():
    gh_repo = FakeGhRepo()
    client = FakeRepoClient()
    record_repo = FakeRecordRepo()
    service = services_module.GithubRepos(gh_repo, client, record_repo)

    # Seed return values
    model_by_id = DummyModel(id=1, name="r1")
    model_by_name = [DummyModel(id=2, name="r2")]
    gh_repo.by_id[1] = model_by_id
    gh_repo.by_name["r2"] = model_by_name

    assert service.get_repo_by_id(1) == model_by_id
    assert service.get_repo_by_name("r2") == model_by_name


def test_create_repo_success_adds_record_and_persists_repo():
    gh_repo = FakeGhRepo()
    client = FakeRepoClient()
    record_repo = FakeRecordRepo(return_id=77)
    service = services_module.GithubRepos(gh_repo, client, record_repo)

    req = DummyRequest(
        name="my-repo",
        repo_link="https://github.com/o/my-repo",
        owner="o",
        description="desc",
        is_fork=False,
        last_updated=datetime(2024, 1, 1, tzinfo=timezone.utc),
        pushed_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        is_archived=False,
        license="Apache-2.0",
        stargazers_count=5,
        watchers_count=6,
        forks_count=7,
        open_issues_count=8,
        network_count=9,
        subscribers_count=10,
        branches_count=3,
    )

    user = "alice"
    result = service.create_repo(req, user)

    # Record repo should have been called
    assert len(record_repo.created) == 1
    created_record = record_repo.created[0]
    # Minimal sanity checks on record fields
    assert created_record.record_type == "REPO" or created_record.record_type == services_module.RecordType.REPO
    assert created_record.source == "GITHUB" or created_record.source == services_module.Source.GITHUB
    assert created_record.status == "PENDING" or created_record.status == services_module.Status.PENDING
    assert created_record.keyword == [req.name]
    assert created_record.created_by == user
    assert created_record.updated_by == user

    # Repo persistence should be called with a GithubRepoModel-dummy
    assert len(gh_repo.created_models) == 1
    created_repo_model = gh_repo.created_models[0]
    assert isinstance(created_repo_model, DummyModel)
    assert created_repo_model.record_id == 77
    assert created_repo_model.name == req.name
    assert created_repo_model.repo_link == req.repo_link
    assert created_repo_model.owner == req.owner
    assert created_repo_model.description == req.description
    assert created_repo_model.is_fork is False
    assert created_repo_model.is_archived is False
    assert created_repo_model.branches_count == 3
    assert created_repo_model.created_by == user
    assert created_repo_model.updated_by == user

    # The returned value is the same model that was created
    assert result == created_repo_model


def test_create_repo_when_record_create_fails_raises_and_does_not_persist_repo():
    gh_repo = FakeGhRepo()
    client = FakeRepoClient()
    record_repo = FakeRecordRepo(raise_exc=True)
    service = services_module.GithubRepos(gh_repo, client, record_repo)

    req = DummyRequest(
        name="broken",
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

    with pytest.raises(RuntimeError):
        service.create_repo(req, "bob")

    # No DB repo create call should have been made
    assert gh_repo.created_models == []


def test_update_repo_returns_none_if_missing_and_does_not_update():
    gh_repo = FakeGhRepo()
    client = FakeRepoClient()
    record_repo = FakeRecordRepo()
    service = services_module.GithubRepos(gh_repo, client, record_repo)

    # No existing repo in by_id
    out = service.update_repo(repo_id=999, updates={"description": "x"}, user="me")
    assert out is None
    assert gh_repo.last_update_id is None


def test_update_repo_updates_with_defaults_and_returns_refreshed_model():
    gh_repo = FakeGhRepo()
    client = FakeRepoClient()
    record_repo = FakeRecordRepo()
    service = services_module.GithubRepos(gh_repo, client, record_repo)

    existing_model = DummyModel(id=10, name="r1")
    gh_repo.by_id[10] = existing_model

    # After update, get_repo_by_id should return the refreshed model
    refreshed_model = DummyModel(id=10, name="r1", description="updated")
    def get_repo_by_id_side_effect(repo_id):
        return refreshed_model
    gh_repo.get_by_id = get_repo_by_id_side_effect  # override to always return refreshed

    result = service.update_repo(10, {"description": "updated"}, user="admin")

    assert gh_repo.last_update_id == 10
    # Should add updated_at and updated_by
    assert "updated_by" in gh_repo.last_update_updates and gh_repo.last_update_updates["updated_by"] == "admin"
    assert "updated_at" in gh_repo.last_update_updates and isinstance(gh_repo.last_update_updates["updated_at"], datetime)
    assert result == refreshed_model


def test_sync_from_json_skips_existing_and_creates_new_with_branch_fallback(monkeypatch):
    gh_repo = FakeGhRepo()
    client = FakeRepoClient()
    record_repo = FakeRecordRepo()
    service = services_module.GithubRepos(gh_repo, client, record_repo)

    # Existing repo should be skipped
    gh_repo.by_name["exists"] = [DummyModel(id=1, name="exists")]

    # Make get_repo_branches raise to trigger fallback to 0
    client.branches_raise = True

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
            "network_count": 0,  # will fall back to forks_count (3)
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
            "network_count": 0,  # -> fall back to forks_count (30)
            "subscribers_count": 50,
        },
    ]

    captured_req = {}
    def fake_create_repo(repo_request, user):
        captured_req["req"] = repo_request
        # Return a dummy created model
        return DummyModel(id=2, name=repo_request.name)

    # Patch the create_repo method of the service to capture the request object
    monkeypatch.setattr(service, "create_repo", fake_create_repo)

    result = service.sync_from_json(repos_data, user="u1")

    # Should create exactly one (skipping 'exists')
    assert len(result) == 1
    assert result[0].name == "new-one"

    req = captured_req["req"]
    assert isinstance(req, DummyRequest)
    # Branch fallback to 0 due to exception
    assert req.branches_count == 0
    # License extraction
    assert req.license == "Apache-2.0"
    # Network count fallback to forks_count
    assert req.network_count == 30
    # Owner and flags mapped
    assert req.owner == "ga4gh"
    assert req.is_fork is False
    assert req.is_archived is True


def test_sync_repos_delegates_to_client_and_calls_sync_from_json(monkeypatch):
    gh_repo = FakeGhRepo()
    client = FakeRepoClient()
    record_repo = FakeRecordRepo()
    service = services_module.GithubRepos(gh_repo, client, record_repo)

    client.repos = [{"name": "a"}, {"name": "b"}]

    called = {}
    def fake_sync_from_json(repos_data, user):
        called["repos_data"] = list(repos_data)
        called["user"] = user
        return ["ok"]

    monkeypatch.setattr(service, "sync_from_json", fake_sync_from_json)

    out = service.sync_repos(user="sam", org="GA4GH")
    assert out == ["ok"]
    assert called["repos_data"] == client.repos
    assert called["user"] == "sam"
    assert client.call_log["get_repos_by_org"] == ["GA4GH"]


def test_sync_single_repo_updates_existing(monkeypatch):
    gh_repo = FakeGhRepo()
    client = FakeRepoClient()
    record_repo = FakeRecordRepo()
    service = services_module.GithubRepos(gh_repo, client, record_repo)

    # Single repo payload coming from client
    client.single_repo = {
        "name": "r1",
        "owner": {"login": "ga4gh"},
        "html_url": "https://github.com/ga4gh/r1",
        "description": "desc",
        "fork": False,
        "updated_at": "2024-03-01T00:00:00Z",
        "pushed_at": "2024-03-02T00:00:00Z",
        "archived": False,
        "license": {"name": "MIT"},
        "stargazers_count": 11,
        "watchers_count": 22,
        "forks_count": 33,
        "open_issues_count": 44,
        "network_count": 55,
        "subscribers_count": 66,
    }
    client.branches_result = 4

    # Existing repo in DB by name
    existing_db_id = 123
    existing = DummyModel(id=existing_db_id, name="r1")
    gh_repo.by_name["r1"] = [existing]
    gh_repo.by_id[existing_db_id] = DummyModel(id=existing_db_id, name="r1", description="desc")

    out = service.sync_single_repo(user="any")

    # Should call update with db id and a dict from model_dump
    assert gh_repo.last_update_id == existing_db_id
    updates = gh_repo.last_update_updates
    assert isinstance(updates, dict)
    assert updates["name"] == "r1"
    assert updates["owner"] == "ga4gh"
    # Branches counted
    assert updates["branches_count"] == 4
    # created_* should not be present
    assert "created_at" not in updates
    assert "created_by" not in updates

    assert out.name == "r1"
    assert out.description == "desc"


def test_sync_single_repo_creates_when_missing(monkeypatch):
    gh_repo = FakeGhRepo()
    client = FakeRepoClient()
    record_repo = FakeRecordRepo(return_id=999)
    service = services_module.GithubRepos(gh_repo, client, record_repo)

    client.single_repo = {
        "name": "newrepo",
        "owner": {"login": "ga4gh"},
        "html_url": "https://github.com/ga4gh/newrepo",
        "description": "",
        "fork": True,
        "updated_at": "2024-04-01T00:00:00Z",
        "pushed_at": "2024-04-02T00:00:00Z",
        "archived": True,
        "license": None,
        "stargazers_count": 1,
        "watchers_count": 2,
        "forks_count": 3,
        "open_issues_count": 4,
        "network_count": 5,
        "subscribers_count": 6,
    }
    client.branches_result = 7

    # No existing repo by name -> create
    gh_repo.by_name["newrepo"] = []

    captured = {}
    def fake_create_repo(repo_request, user):
        captured["req"] = repo_request
        return DummyModel(id=888, name=repo_request.name)

    monkeypatch.setattr(service, "create_repo", fake_create_repo)

    out = service.sync_single_repo(user="creator")
    assert out.name == "newrepo"
    assert captured["req"].branches_count == 7
    assert captured["req"].owner == "ga4gh"
    assert captured["req"].is_fork is True
    assert captured["req"].is_archived is True