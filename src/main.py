import uvicorn
from fastapi import FastAPI

from .clients import cats
from .config.config import config
from .config.constants import CATS_BASE_URL
from .models.animal import Animal
from .repositories import setup, sqlbuilder
from .repositories.animals import Animals as AnimalRepo
from .routers.animals import Animals as AnimalRouter
from .services.animals import Animals as AnimalService


def main() -> FastAPI:
    db_conn = setup.DatabaseConnection(config.database_url)
    db_conn.connect()

    cats_client = cats.Cats(CATS_BASE_URL, config.cats_api_key)

    animals_fields = set(Animal.model_fields.keys())
    animals_sql_builder = sqlbuilder.SQLBuilder("animals").allow_fields(animals_fields - {"id"})
    animals_repo = AnimalRepo(db_conn, animals_sql_builder)
    animals_service = AnimalService(animals_repo, cats_client)
    animals_router = AnimalRouter(animals_service)

    app = FastAPI()
    app.include_router(animals_router.router)

    return app

if __name__ == "__main__":
    app = main()
    uvicorn.run(app, host=config.host, port=config.port, reload=config.debug)
