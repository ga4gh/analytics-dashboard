import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL",
                                      "postgresql://postgres:pgpass@localhost:5432/analytics_dev")

        self.cats_api_key = os.getenv("CATS_API_KEY", "")
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8080"))
        self.debug = os.getenv("DEBUG", "False").lower() == "true"

config = Config()
