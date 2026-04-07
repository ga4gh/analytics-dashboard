from fastapi import APIRouter, HTTPException, Response, Body
from sqlalchemy.orm import Session
import json
from datetime import datetime

from src.models.pmc_article import PMCArticle, PMCArticleFull, PMCArticleListResponse
from src.models.pmc_author import PMCAuthor
from src.models.citation import Citation as CitationModel, CitationList
from src.services.epmc import EPMCService as EPMCService
from src.repositories.epmc import EPMCRepo as EPMCRepo
from src.services.grant import GrantService as Grant
from src.config.session import get_session


router = APIRouter(prefix="/epmc", tags=["Articles"])

class EPMC:
    def __init__(self, epmc_service: EPMCService, db: Session):
        self.router = APIRouter()
        self.epmc_service = epmc_service
        self.db = db
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get("/epmc/all-articles", response_model=PMCArticleListResponse)
        async def get_all_articles(limit: int = 1000, skip: int = 0):
            try:
                repo = EPMCRepo(self.db)
                articles = repo.get_all_articles(limit=limit, skip=skip)
                article_count = repo.get_total_unique_articles_count()

                validated: list[PMCArticleFull] = []
                for a in articles:
                    # Normalize pub_type: DB may store arrays or lists; ensure a string for response
                    pt = getattr(a, "pub_type", None)
                    if isinstance(pt, (list, tuple)):
                        setattr(a, "pub_type", pt[0] if len(pt) > 0 else None)

                    # Convert ORM entity to Pydantic model
                    validated.append(PMCArticleFull.model_validate(a))

                return {"article_count": article_count, "articles": validated}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch articles: {str(e)}")

        @self.router.get("/epmc/all-grants")
        async def get_all_grants(limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            return repo.get_all_grants(limit=limit, skip=skip)

        @self.router.get("/epmc/all-pmc-authors")
        async def get_all_pmc_authors(limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            return repo.get_all_pmc_authors(limit=limit, skip=skip)

        @self.router.get("/epmc/get-authors-by-article-id/{article_id}", response_model=list[PMCAuthor]) # to be fixed
        async def get_authors_by_article_id(article_id: int, limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            return repo.get_authors_by_article_id(article_id, limit=limit, skip=skip)

        @self.router.get("/epmc/get-articles-by-author-id/{author_id}", response_model=list[PMCArticle]) # to be fixed
        async def get_articles_by_author_id(author_id: int, limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            return repo.get_articles_by_author_id(author_id, limit=limit, skip=skip)

        @self.router.get("/epmc/get-articles-by-keyword/{keyword}", response_model=list[PMCArticle]) # to be fixed
        async def get_articles_by_keyword(keyword: str, limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            return repo.get_articles_by_keyword(keyword, limit=limit, skip=skip)

        @self.router.get("/epmc/all-article-authors")
        async def get_all_article_authors(limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            return repo.get_all_article_authors(limit=limit, skip=skip)

        @self.router.get("/epmc/all-pmc-references")
        async def get_all_pmc_references(limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            return repo.get_all_pmc_references(limit=limit, skip=skip)

        @self.router.get("/epmc/all-citations")
        async def get_all_citations(limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            return repo.get_all_citations(limit=limit, skip=skip)

        @self.router.get("/epmc/all-fulltexts")
        async def get_all_fulltexts(limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            return repo.get_all_fulltexts(limit=limit, skip=skip)

        @self.router.get("/epmc/all-pmc-affiliations")
        async def get_all_pmc_affiliations(limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            return repo.get_all_pmc_affiliations(limit=limit, skip=skip)

        @self.router.post("/epmc/ingest-pmc-data", response_model=list[PMCArticleFull])
        async def ingest_pmc_data(
            keyword: str = Body(..., embed=True),
        ):
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            grant_service = Grant(repo)

            try:
                print("ingesting")
                result = service.insert_articles_by_keyword(keyword, created_by="system", epmc_db=self.db)
                #citations_result = service.insert_citations(created_by="system")
                references_result = service.insert_references(created_by="system")
                grant_result = grant_service.create_grants(keyword)

                # Write a JSON-line entry with ingestion results and timestamp.
                try:
                    log_entry = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "keyword": keyword,
                        "articles": result,
                        #"citations": citations_result,
                        "references": references_result,
                        "grants": grant_result,
                    }
                    with open("ingestion_log.txt", "a", encoding="utf-8") as lf:
                        lf.write(json.dumps(log_entry, default=str) + "\n")
                except Exception:
                    # Don't let logging failures break ingestion
                    pass
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

            articles = repo.get_all_articles()
            return [PMCArticleFull.model_validate(article) for article in articles]

        @self.router.post("/epmc/ingest-pmc-grants")
        async def ingest_pmc_grants(keyword: str = Body(..., embed=True)):
            """Ingest grants from Europe PMC for a given keyword using GrantService.create_grants."""
            repo = EPMCRepo(self.db)
            grant_service = Grant(repo)

            try:
                print("ingesting grants")
                result = grant_service.create_grants(keyword)

                # Write a JSON-line entry with ingestion results and timestamp.
                try:
                    log_entry = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "keyword": keyword,
                        "grants": result,
                    }
                    with open("ingestion_log.txt", "a", encoding="utf-8") as lf:
                        lf.write(json.dumps(log_entry, default=str) + "\n")
                except Exception:
                    pass
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Grant ingestion failed: {e}")

            return result

        @self.router.post("/epmc/ingest-pmc-references")
        async def ingest_pmc_references(use_db_articles: bool = True):
            """Ingest references for all articles in the database using EPMCService.insert_references."""
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)

            try:
                print("ingesting references")
                result = service.insert_references(created_by="system", use_db_articles=use_db_articles)

                # Write a JSON-line entry with ingestion results and timestamp.
                try:
                    log_entry = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "references": result,
                        "use_db_articles": use_db_articles,
                    }
                    with open("ingestion_log.txt", "a", encoding="utf-8") as lf:
                        lf.write(json.dumps(log_entry, default=str) + "\n")
                except Exception:
                    pass
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Reference ingestion failed: {e}")

            return result
        
        @self.router.get("/epmc/all-latest-entries")
        async def get_all_latest_entries(limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            return repo.get_all_latest_entries(limit=limit, skip=skip)
        
        @self.router.get("/epmc/article/{pm_id}/latest-entries")
        async def get_article_latest_entries(pm_id: str, limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            return repo.get_all_latest_entries(pm_id=pm_id, limit=limit, skip=skip)
        
        @self.router.get("/epmc/affiliation-countries-count")
        async def get_affiliation_countries_count():
            repo = EPMCRepo(self.db)
            return repo.get_affiliation_countries_count()        
        
        @self.router.get("/epmc/unique-citations", response_model=CitationList)
        async def get_unique_citations(limit: int = 1000, skip: int = 0):
            repo = EPMCRepo(self.db)
            citations = repo.get_unique_citations(limit=limit, skip=skip)
            citation_count = repo.get_total_cited_by_count()
            return CitationList(citations=[CitationModel.model_validate(c) for c in citations], citation_count=citation_count)

        @self.router.get("/epmc/top-authors")
        async def get_top_authors(count: int = 15):
            """Return top `count` authors ordered by number of article associations."""
            repo = EPMCRepo(self.db)
            try:
                return repo.get_top_authors(count=count)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch top authors: {e}")
            
        @self.router.get("/epmc/unique-authors-count")
        async def unique_authors_count():
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            
            count = service.get_unique_authors_count()
            return {"unique_authors": count}
        
        @self.router.get("/epmc/get-articles-count")
        async def get_articles_count():
            repo = EPMCRepo(self.db)
            service = EPMCService(repo)
            count = service.get_articles_count()
            return {"articles_count": count} 
