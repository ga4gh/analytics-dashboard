import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL",
                                      "postgresql://pgadmin:admin@localhost:5432/analytics")

        self.pubmed_api_key = os.getenv("PUBMED_API_KEY", "")

        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.debug = os.getenv("DEBUG", "False").lower() == "true"

config = Config()
