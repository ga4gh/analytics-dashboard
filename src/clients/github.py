import requests
from typing import List, Dict, Any
from src.config import constants


class GithubRepoClient:
    def __init__(self, base_url: str, api_key: str, org: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.org = org

    def _headers(self):
        return {"x-api-key": self.api_key} if self.api_key else {}

    def get_gh_repos(self) -> List[Dict[str, Any]]:
        """
        Return all repos for the configured organization using GitHub pagination.
        """
        url = f"{self.base_url}/orgs/{self.org}/repos"
        headers = self._headers()
        params = {"per_page": 100, "page": 1}

        all_repos: List[Dict[str, Any]] = []
        while True:
            resp = requests.get(url, headers=headers, params=params, timeout=120)
            resp.raise_for_status()
            page = resp.json()
            all_repos.extend(page)
            if "next" not in resp.links:
                break
            params["page"] += 1

        return all_repos

    def get_single_repo(self) -> Dict[str, Any]:
        url = f"{self.base_url}{constants.GH_SINGLE_REPO_ENDPOINT}"
        headers = self._headers()
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def get_repo_branches(self, owner: str, repo: str) -> int:
        """Return the total number of branches for a repository (uses pagination)."""
        url = f"{self.base_url}/repos/{owner}/{repo}/branches"
        headers = self._headers()
        params = {"per_page": 100, "page": 1}
        total_branches = 0
        while True:
            resp = requests.get(url, headers=headers, params=params, timeout=120)
            resp.raise_for_status()
            branches = resp.json()
            total_branches += len(branches)
            if "next" not in resp.links:
                break
            params["page"] += 1
        return total_branches


class GithubEntityClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def get_gh_repo_collaborators(self):
        url = f"{self.base_url}{constants.GH_REPO_COLLABORATORS}"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()


class GithubEntityActionsClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def get_gh_repo_stargazers(self):
        url = f"{self.base_url}{constants.GH_REPO_STARGAZERS}"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()


class GithubArchivedStatsClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def get_gh_weekly_commit(self):
        url = f"{self.base_url}{constants.GH_WEEKLY_COMMIT}"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def get_gh_yearly_commit_count(self):
        url = f"{self.base_url}{constants.GH_YEARLY_COMMIT}"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def get_gh_daily_clone_count(self):
        url = f"{self.base_url}{constants.GH_DAILY_CLONE_COUNT}"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def get_gh_daily_view_count(self):
        url = f"{self.base_url}{constants.GH_DAILY_VIEW_COUNT}"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def get_gh_last_14_day_referral_source(self):
        url = f"{self.base_url}{constants.GH_LAST_14_DAY_SOURCE}"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def get_gh_last_14_day_referral_path(self):
        url = f"{self.base_url}{constants.GH_LAST_14_DAY_PATH}"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        resp = requests.get(url, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()
