import os
import pytest

from src.clients.github import (
    GithubRepoClient,
    GithubEntityActionsClient,
)
from src.config import constants

BASE_URL = "https://api.github.com"
#RUN_LIVE = os.environ.get("RUN_LIVE_TESTS") == "1"
RUN_LIVE = True

@pytest.mark.integration
@pytest.mark.skipif(not RUN_LIVE, reason="Set RUN_LIVE_TESTS=1 to run live GitHub API tests")
def test_live_get_repos_by_org_ga4gh():
    client = GithubRepoClient(base_url=BASE_URL, api_key="")  # unauthenticated; OK for public endpoints
    repos = client.get_repos_by_org("GA4GH")

    assert isinstance(repos, list)
    assert len(repos) > 0

    # Basic shape checks for a few items
    sample = repos[0]
    assert isinstance(sample, dict)
    assert "name" in sample
    assert "owner" in sample and isinstance(sample["owner"], dict)


@pytest.mark.integration
@pytest.mark.skipif(not RUN_LIVE, reason="Set RUN_LIVE_TESTS=1 to run live GitHub API tests")
def test_live_get_repo_branches_counts_for_known_public_repo():
    client = GithubRepoClient(base_url=BASE_URL, api_key="")
    # Use a well-known public repo with at least one branch
    total = client.get_repo_branches(owner="octocat", repo="Hello-World")
    assert isinstance(total, int)
    assert total >= 1


@pytest.mark.integration
@pytest.mark.skipif(not RUN_LIVE, reason="Set RUN_LIVE_TESTS=1 to run live GitHub API tests")
def test_live_get_single_repo_via_constant_endpoint():
    client = GithubRepoClient(base_url=BASE_URL, api_key="")
    # Point the constant to a known public repo
    constants.GH_SINGLE_REPO_ENDPOINT = "/repos/octocat/Hello-World"

    data = client.get_single_repo()
    assert isinstance(data, dict)
    assert data.get("name") == "Hello-World"
    # 'full_name' usually 'octocat/Hello-World'
    assert "full_name" in data and data["full_name"].endswith("/Hello-World")


@pytest.mark.integration
@pytest.mark.skipif(not RUN_LIVE, reason="Set RUN_LIVE_TESTS=1 to run live GitHub API tests")
def test_live_stargazers_for_known_public_repo():
    actions_client = GithubEntityActionsClient(base_url=BASE_URL, api_key="")
    constants.GH_REPO_STARGAZERS = "/repos/octocat/Hello-World/stargazers"

    data = actions_client.get_gh_repo_stargazers()
    # Public endpoint should return a list (may be empty)
    assert isinstance(data, list)
    # If there are items, they should be dicts with user info
    if data:
        assert isinstance(data[0], dict)
        # Common keys in stargazer entries can vary; check that at least some keys exist
        assert any(k in data[0] for k in ("login", "user", "id"))