from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from src.config.session import get_session
from src.models.pmc_article import PMCArticle, PMCArticleFull
from src.services.epmc import EPMCService as EPMCService
from src.repositories.epmc import EPMCRepo as EPMCRepo


router = APIRouter(prefix="/epmc", tags=["Articles"])

class EPMC:
    def __init__(self, epmc_service: EPMCService):
        self.router = APIRouter()
        self.epmc_service = epmc_service
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get("/all-articles", response_model=list[PMCArticleFull])
        async def get_all_articles(db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return service.get_all_articles()