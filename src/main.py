import uvicorn
from fastapi import FastAPI
from src.config.config import config
from src.repositories import setup, sqlbuilder
from src.routers.pypi import Pypi as PypiRouter
from src.services.pypi import Pypi as PypiService
from src.repositories.pypi import Pypi as PypiRepo
from src.models.pypi import Pypi as PypiModel
from contextlib import asynccontextmanager

def main() -> FastAPI:
    db_conn = setup.DatabaseConnection(config.database_url)
    db_conn.connect()
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db_conn.connect()
        print("Database connected")
        yield
        try:
            db_conn.disconnect()
            print("Database disconnected")
        except RuntimeError:
            pass

    pypi_fields = set(PypiModel.model_fields.keys())
    pypi_sql_builder = sqlbuilder.SQLBuilder("pypi").allow_fields(pypi_fields)
    pypi_repo = PypiRepo(db_conn, pypi_sql_builder)
    pypi_service = PypiService(pypi_repo)
    pypi_router = PypiRouter(pypi_service)

    app = FastAPI(lifespan=lifespan)
    app.include_router(pypi_router.router)

    for r in app.routes:
        print(r.path, r.methods)
        
    return app

if __name__ == "__main__":
    app = main()
    uvicorn.run(app, host=config.host, port=config.port, reload=False)
