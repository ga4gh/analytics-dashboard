from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    class Config:
        env_prefix = "DB_"
        env_file = ".env"


db_settings = DatabaseSettings()
