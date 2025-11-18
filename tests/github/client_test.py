import pytest
import requests

from src.clients.github import (
    GithubRepoClient,
    GithubEntityClient,
    GithubEntityActionsClient,
    GithubArchivedStatsClient,
)
from src.config import constants


class MockResponse:
    def __init__(self, json_data, links=None, status_code=200):
        self._json = json_data
        self.links = links or {}
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def test_get_gh_repos_paginates_and_aggregates(monkeypatch):
    base_url = "https://api.github.com"
    api_key = "secret"
    org = "GA4GH"

    call_log = []

    responses = [
        MockResponse([{"id": 1, "name": "repo-1"}], links={"next": {"url": "next-page"}}),
        MockResponse([{"id": 2, "name": "repo-2"}], links={}),
    ]

    def mock_get(url, headers=None, params=None, timeout=None):
        # capture call details
        call_log.append({"url": url, "headers": headers, "params": dict(params or {})})
        # simulate pagination sequence
        return responses.pop(0)

    monkeypatch.setattr(requests, "get", mock_get)

    client = GithubRepoClient(base_url=base_url, api_key=api_key)
    repos = client.get_repos_by_org(org)

    # Aggregated results (two pages combined)
    assert isinstance(repos, list)
    assert len(repos) == 2
    assert repos[0]["name"] == "repo-1"
    assert repos[1]["name"] == "repo-2"

    # Verify correct URL and paging order
    assert all(call["url"] == f"{base_url}/orgs/{org}/repos" for call in call_log)
    assert [call["params"]["page"] for call in call_log] == [1, 2]
    # Verify headers include api key
    assert all(call["headers"].get("x-api-key") == api_key for call in call_log)


def test_get_gh_repos_raises_on_http_error(monkeypatch):
    base_url = "https://api.github.com"
    client = GithubRepoClient(base_url=base_url, api_key="")

    def mock_get(url, headers=None, params=None, timeout=None):
        return MockResponse([], status_code=500)

    monkeypatch.setattr(requests, "get", mock_get)

    with pytest.raises(requests.HTTPError):
        client.get_repos_by_org(org="org")


def test_get_repo_by_keyword_paginates_and_returns_list(monkeypatch):
    base_url = "https://api.github.com"
    api_key = "k"
    client = GithubRepoClient(base_url=base_url, api_key=api_key)

    call_log = []
    responses = [
        MockResponse([{"full_name": "o/repo1"}], links={"next": {"url": "n"}}),
        MockResponse([{"full_name": "o/repo2"}], links={}),
    ]

    def mock_get(url, headers=None, params=None, timeout=None):
        call_log.append({"url": url, "headers": headers, "params": dict(params or {})})
        return responses.pop(0)

    monkeypatch.setattr(requests, "get", mock_get)

    result = client.get_repos_by_keyword("workflow")

    assert isinstance(result, list)
    assert len(result) == 2
    # Verify constructed search URL
    assert all(
        call["url"] == f"{base_url}/search/repositories?q=workflow" for call in call_log
    )
    # Verify pagination occurred
    assert [call["params"]["page"] for call in call_log] == [1, 2]
    # Verify auth header
    assert all(call["headers"].get("x-api-key") == api_key for call in call_log)


def test_get_single_repo_uses_constant_endpoint(monkeypatch):
    base_url = "https://api.github.com"
    api_key = "abc"
    # Ensure the constant exists for the test
    constants.GH_SINGLE_REPO_ENDPOINT = "/repos/GA4GH/some-repo"

    call_log = {}

    def mock_get(url, headers=None, timeout=None):
        call_log["url"] = url
        call_log["headers"] = headers
        return MockResponse({"name": "some-repo"})

    monkeypatch.setattr(requests, "get", mock_get)

    client = GithubRepoClient(base_url=base_url, api_key=api_key)
    data = client.get_single_repo()

    assert data == {"name": "some-repo"}
    assert call_log["url"] == f"{base_url}{constants.GH_SINGLE_REPO_ENDPOINT}"
    assert call_log["headers"]["x-api-key"] == api_key


def test_get_repo_branches_counts_across_pages(monkeypatch):
    base_url = "https://api.github.com"
    api_key = ""
    client = GithubRepoClient(base_url=base_url, api_key=api_key)

    call_pages = []

    responses = [
        MockResponse([{"name": "main"}, {"name": "dev"}], links={"next": {"url": "n"}}),
        MockResponse([{"name": "release"}], links={}),
    ]

    def mock_get(url, headers=None, params=None, timeout=None):
        call_pages.append(params["page"])
        return responses.pop(0)

    monkeypatch.setattr(requests, "get", mock_get)

    total = client.get_repo_branches(owner="GA4GH", repo="spec")
    assert total == 3
    assert call_pages == [1, 2]


def test_entity_client_collaborators(monkeypatch):
    base_url = "https://api.example.com"
    api_key = "tok"
    constants.GH_REPO_COLLABORATORS = "/repos/o/r/collaborators"

    seen = {}

    def mock_get(url, headers=None, timeout=None):
        seen["url"] = url
        seen["headers"] = headers
        return MockResponse([{"login": "alice"}, {"login": "bob"}])

    monkeypatch.setattr(requests, "get", mock_get)

    client = GithubEntityClient(base_url=base_url, api_key=api_key)
    data = client.get_gh_repo_collaborators()

    assert data == [{"login": "alice"}, {"login": "bob"}]
    assert seen["url"] == f"{base_url}{constants.GH_REPO_COLLABORATORS}"
    assert seen["headers"].get("x-api-key") == api_key


def test_actions_client_stargazers(monkeypatch):
    base_url = "https://api.github.com"
    api_key = "tok"
    constants.GH_REPO_STARGAZERS = "/repos/o/r/stargazers"

    captured = {}

    def mock_get(url, headers=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        return MockResponse([{"user": "carol"}])

    monkeypatch.setattr(requests, "get", mock_get)

    client = GithubEntityActionsClient(base_url=base_url, api_key=api_key)
    data = client.get_gh_repo_stargazers()

    assert data == [{"user": "carol"}]
    assert captured["url"] == f"{base_url}{constants.GH_REPO_STARGAZERS}"
    assert captured["headers"].get("x-api-key") == api_key


@pytest.mark.parametrize(
    "method_name,const_attr,payload",
    [
        ("get_gh_weekly_commit", "GH_WEEKLY_COMMIT", {"weekly": [1, 2, 3]}),
        ("get_gh_yearly_commit_count", "GH_YEARLY_COMMIT", {"yearly": [5, 6]}),
        ("get_gh_daily_clone_count", "GH_DAILY_CLONE_COUNT", {"clones": [10]}),
        ("get_gh_daily_view_count", "GH_DAILY_VIEW_COUNT", {"views": [7]}),
        ("get_gh_last_14_day_referral_source", "GH_LAST_14_DAY_SOURCE", {"sources": []}),
        ("get_gh_last_14_day_referral_path", "GH_LAST_14_DAY_PATH", {"paths": []}),
    ],
)
def test_archived_stats_endpoints(monkeypatch, method_name, const_attr, payload):
    base_url = "https://api.github.com"
    api_key = "k"

    # Ensure the constant exists and points to a known path
    setattr(constants, const_attr, f"/{const_attr.lower()}")

    seen = {}

    def mock_get(url, headers=None, timeout=None):
        seen["url"] = url
        seen["headers"] = headers
        return MockResponse(payload)

    monkeypatch.setattr(requests, "get", mock_get)

    client = GithubArchivedStatsClient(base_url=base_url, api_key=api_key)
    method = getattr(client, method_name)
    result = method()

    assert result == payload
    assert seen["url"] == f"{base_url}{getattr(constants, const_attr)}"
    assert seen["headers"].get("x-api-key") == api_key