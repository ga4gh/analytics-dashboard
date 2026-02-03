from fastapi import APIRouter, Depends, HTTPException, Response, Body
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
        @self.router.get("/epmc/all-articles", response_model=list[PMCArticleFull])
        async def get_all_articles(db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return service.get_all_articles()

        @self.router.post("/epmc/ingest-pmc-data", response_model=list[PMCArticleFull])
        async def ingest_pmc_data(
            keyword: str = Body(..., embed=True),  
            db: Session = Depends(get_session),
        ):
            repo = EPMCRepo(db)
            service = EPMCService(repo)

            try:
                service.insert_articles_by_keyword(keyword, created_by="system", epmc_db=db)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

            articles = service.get_all_articles()
            return [PMCArticleFull.model_validate(article) for article in articles]
