import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL",
                                      "postgresql://analytics_staging:##R)n\u0026oN[a2+=}\u003eNWCNK@analytics-staging.c0q4keadjybw.us-east-2.rds.amazonaws.com:5432/analytics")

        self.cats_api_key = os.getenv("CATS_API_KEY", "")
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8080"))
        self.debug = os.getenv("DEBUG", "False").lower() == "true"

config = Config()
