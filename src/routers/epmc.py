from fastapi import APIRouter, Depends, HTTPException, Response, Body
from sqlalchemy.orm import Session

from src.config.session import get_session
from src.models.pmc_article import PMCArticle, PMCArticleFull
from src.models.pmc_author import PMCAuthor
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
            return repo.get_all_articles()

        @self.router.get("/epmc/all-grants")
        async def get_all_grants(db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return repo.get_all_grants()

        @self.router.get("/epmc/all-pmc-authors")
        async def get_all_pmc_authors(db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return repo.get_all_pmc_authors()

        @self.router.get("/epmc/get-authors-by-article-id/{article_id}", response_model=list[PMCAuthor])
        async def get_authors_by_article_id(article_id: int, db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return repo.get_authors_by_article_id(article_id)

        @self.router.get("/epmc/get-articles-by-author-id/{author_id}", response_model=list[PMCArticle])
        async def get_articles_by_author_id(author_id: int, db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return repo.get_articles_by_author_id(author_id)

        @self.router.get("/epmc/get-articles-by-keyword/{keyword}", response_model=list[PMCArticle])
        async def get_articles_by_keyword(keyword: str, db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return repo.get_articles_by_keyword(keyword)

        @self.router.get("/epmc/all-article-authors")
        async def get_all_article_authors(db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return repo.get_all_article_authors()

        @self.router.get("/epmc/all-pmc-references")
        async def get_all_pmc_references(db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return repo.get_all_pmc_references()

        @self.router.get("/epmc/all-citations")
        async def get_all_citations(db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return repo.get_all_citations()

        @self.router.get("/epmc/all-fulltexts")
        async def get_all_fulltexts(db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return repo.get_all_fulltexts()

        @self.router.get("/epmc/all-pmc-affiliations")
        async def get_all_pmc_affiliations(db: Session = Depends(get_session)):
            repo = EPMCRepo(db)
            service = EPMCService(repo)
            return repo.get_all_pmc_affiliations()

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

            articles = repo.get_all_articles()
            return [PMCArticleFull.model_validate(article) for article in articles]
