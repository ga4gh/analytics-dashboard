from fastapi import APIRouter, HTTPException, Response
from src.models.pmc_article import PMCArticle
from src.services.epmc import EPMCService as EPMCService


class EPMC:
    def __init__(self, epmc_service: EPMCService):
        self.router = APIRouter()
        self.epmc_service = epmc_service
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get("/epmc/all-articles", response_model=PMCArticle)
        async def get_all_articles():
            pass