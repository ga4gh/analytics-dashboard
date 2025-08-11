import requests

from src.config import constants


class Cats:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.api_key = api_key

    def get_cat_breeds(self) -> dict:
        url = f"{self.base_url}{constants.CATS_BREED_ENDPOINT}"
        headers = {"x-api-key": self.api_key}

        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()

        return response.json()
