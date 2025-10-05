from datetime import UTC, datetime

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

from src.models.article import Article
from src.services.pubmed import Pubmed as PubmedService


# Request/Response models
class InsertArticlesRequest(BaseModel):
    keyword: str
    pubmed_db: str = "pubmed"


class InsertArticlesResponse(BaseModel):
    processed: int
    created: int
    updated: int
    skipped: int

START_DATE_QUERY = Query(None, description="Start date (ISO format)")
END_DATE_QUERY = Query(None, description="End date (ISO format), defaults to today")
STATUS_QUERY = Query(None, description="Filter by article status")
class Pubmed:
    def __init__(self, pubmed_service: PubmedService) -> None:
        self.router = APIRouter()
        self.pubmed_service = pubmed_service
        self._setup_routes()

    def _setup_routes(self) -> None:

        @self.router.post("/pubmed/articles", response_model=InsertArticlesResponse)
        async def insert_articles_by_keyword(
            request: InsertArticlesRequest,
            user: str = Header(...)
        ) -> InsertArticlesResponse:
            try:
                result = self.pubmed_service.insert_articles_by_keyword(
                    keyword=request.keyword,
                    created_by=user,
                    pubmed_db=request.pubmed_db
                )
                return InsertArticlesResponse(**result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.get("/pubmed/articles/{keyword}", response_model=list[Article])
        async def get_articles(
            keyword: str,
            start_date: datetime = START_DATE_QUERY,
            end_date: datetime = END_DATE_QUERY,
            status: str = STATUS_QUERY
        ) -> list[Article]:
            try:
                # Route to appropriate method based on query parameters
                if start_date is not None:
                    # Date filtering
                    if end_date is None:
                        end_date = datetime.now(tz=UTC)

                    if start_date >= end_date:
                        raise HTTPException(status_code=400, detail="Start date must be before end date") # noqa: TRY301

                    articles = self.pubmed_service.get_articles_by_keyword_and_date(
                        keyword=keyword,
                        start_date=start_date,
                        end_date=end_date
                    )
                elif status is not None:
                    # Status filtering
                    articles = self.pubmed_service.get_articles_by_keyword_and_status(
                        keyword=keyword,
                        status=status
                    )
                else:
                    # Basic keyword search
                    articles = self.pubmed_service.get_articles_by_keyword(keyword=keyword)

                if not articles:
                    raise HTTPException(status_code=404, detail="No articles found for criteria") # noqa: TRY301
                return articles  # noqa: TRY300
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) from e
