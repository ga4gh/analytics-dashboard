import uvicorn
from fastapi import FastAPI
from .repositories import setup, animals as animalRepo
from .services import animals as animalsService
from .routers import animals as animalsRouter
from .clients import cats
from .config.config import config
from .config.constants import CATS_BASE_URL


def main():
    db_conn = setup.DatabaseConnection(config.database_url)
    db_conn.connect()

    cats_client = cats.Cats(CATS_BASE_URL, config.cats_api_key)

    animals_repo = animalRepo.Animals(db_conn, "animals")
    animals_service = animalsService.Animals(animals_repo, cats_client)
    animals_router = animalsRouter.Animals(animals_service)

    app = FastAPI()
    app.include_router(animals_router.router)

    return app

if __name__ == "__main__":
    app = main()
    uvicorn.run(app, host=config.host, port=config.port, reload=config.debug)
