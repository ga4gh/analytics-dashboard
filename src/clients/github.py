import requests
from src.config import constants

class Github:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    def get_gh_repos(self):
        url = f"{self.base_url}{constants.GH_REPOS_ENDPOINT}"
        headers = {"x-api-key": self.api_key}

        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        return response.json()

    """ def get_gh_repo_entity(self):
        url = f"{self.base_url}{constants.GH_REPO_ENTITY_ENDPOINT}"
        headers = {"x-api-key": self.api_key}

        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        return response.json() """

    """ def get_gh_repo_entity_actions(self):
        url = f"{self.base_url}{constants.GH_REPO_ENTITY_ACTIONS_ENDPOINT}"
        headers = {"x-api-key": self.api_key}

        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        return response.json() """

    def get_gh_weekly_commit(self):
        url = f"{self.base_url}{constants.GH_WEEKLY_COMMIT}"
        headers = {"x-api-key": self.api_key}

        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        return response.json()

    def get_gh_yearly_commit_count(self):
        url = f"{self.base_url}{constants.GH_YEARLY_COMMIT}"
        headers = {"x-api-key": self.api_key}

        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        return response.json()

    def get_gh_daily_clone_count(self):
        url = f"{self.base_url}{constants.GH_DAILY_CLONE_COUNT}"
        headers = {"x-api-key": self.api_key}

        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        return response.json()

    def get_gh_daily_view_count(self):
        url = f"{self.base_url}{constants.GH_DAILY_VIEW_COUNT}"
        headers = {"x-api-key": self.api_key}

        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        return response.json()

    def get_gh_last_14_day_referral_source(self):
        url = f"{self.base_url}{constants.GH_LAST_14_DAY_SOURCE}"
        headers = {"x-api-key": self.api_key}

        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        return response.json()

    def get_gh_last_14_day_referral_path(self):
        url = f"{self.base_url}{constants.GH_LAST_14_DAY_PATH}"
        headers = {"x-api-key": self.api_key}

        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        return response.json()