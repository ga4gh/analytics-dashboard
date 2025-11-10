import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException

from src.routers.pubmed import Pubmed
from src.models.pubmed_requests import InsertArticlesRequest, InsertArticlesResponse
from src.services.pubmed import Pubmed as PubmedService
from src.models.article import Article, Status
from src.models.author import Author, ArticleType
from src.models.affiliation import Affiliation


class TestPubmed:
    
    @pytest.fixture
    def mock_pubmed_service(self):
        return Mock(spec=PubmedService)
    
    @pytest.fixture
    def pubmed_router(self, mock_pubmed_service):
        return Pubmed(mock_pubmed_service)
    
    @pytest.fixture
    def sample_article(self):
        return Article(
            id=1,
            record_id=101,
            title="GA4GH Beacon: Discovery and Sharing Genomic Data",
            abstract="The GA4GH Beacon protocol enables discovery of genetic variants across federated genomic datasets while preserving privacy and enabling global collaboration in genomic research.",
            journal="Nature Biotechnology",
            source_id="12345678",
            doi="10.1038/s41587-024-02345-6",
            status=Status.PUBLISHED,
            publish_date=datetime(2025, 6, 15, tzinfo=UTC),
            link="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            authors=[
                Author(
                    id=1,
                    article_id=1,
                    name="Name",
                    contact="name@genomics.org",
                    is_primary=True,
                    article_type=ArticleType.ARTICLE,
                    created_at=datetime(2025, 6, 1, tzinfo=UTC),
                    created_by="user"
                ),
                Author(
                    id=2,
                    article_id=1,
                    name="Name",
                    contact="name1@bioinfo.edu",
                    is_primary=False,
                    article_type=ArticleType.ARTICLE,
                    created_at=datetime(2025, 6, 1, tzinfo=UTC),
                    created_by="user"
                )
            ],
            created_at=datetime(2025, 6, 1, tzinfo=UTC),
            created_by="test_user",
            updated_at=datetime(2025, 6, 2, tzinfo=UTC),
            updated_by="test_user",
            version=1
        )
    
    @pytest.fixture
    def sample_articles(self, sample_article):
        return [
            sample_article,
            Article(
                id=2,
                record_id=102,
                title="GA4GH DRS: Data Repository Service for Cloud-Based Genomics",
                abstract="The GA4GH Data Repository Service (DRS) API provides a generic interface to data repositories enabling discovery and access to genomic data in a cloud-agnostic manner.",
                journal="Genome Research",
                source_id="87654321",
                doi="10.1101/gr.298765.124",
                status=Status.PUBLISHED,
                publish_date=datetime(2025, 8, 20, tzinfo=UTC),
                link="https://pubmed.ncbi.nlm.nih.gov/87654321/",
                authors=[
                    Author(
                        id=3,
                        article_id=2,
                        name="name",
                        contact="name@ga4gh.org",
                        is_primary=True,
                        article_type=ArticleType.ARTICLE,
                        created_at=datetime(2025, 8, 1, tzinfo=UTC),
                        created_by="user"
                    ),
                    Author(
                        id=4,
                        article_id=2,
                        name="name",
                        contact="name2@ga4gh.org",
                        is_primary=False,
                        article_type=ArticleType.ARTICLE,
                        created_at=datetime(2025, 8, 1, tzinfo=UTC),
                        created_by="system"
                    )
                ],
                created_at=datetime(2025, 8, 1, tzinfo=UTC),
                created_by="test_user",
                updated_at=datetime(2025, 8, 2, tzinfo=UTC),
                updated_by="test_user",
                version=1
            )
        ]

    @pytest.mark.parametrize("keyword,pubmed_db,user", [
        ("ga4gh", "pubmed", "test_user"),
        ("ga4gh", "pmc", "test_user"),
        ("ga4gh beacon", "pubmed", "test_user"),
        ("ga4gh drs", "pubmed", "test_user")
    ])
    @pytest.mark.asyncio
    async def test_insert_articles_by_keyword_success(self, pubmed_router, mock_pubmed_service, keyword, pubmed_db, user):
        service_result = {
            "processed": 100,
            "created": 80,
            "updated": 15,
            "skipped": 5
        }
        mock_pubmed_service.insert_articles_by_keyword.return_value = service_result
        
        request = InsertArticlesRequest(keyword=keyword, pubmed_db=pubmed_db)
        
        insert_handler = None
        for route in pubmed_router.router.routes:
            if route.path == "/pubmed/articles" and "POST" in route.methods:
                insert_handler = route.endpoint
                break
        
        assert insert_handler is not None
        
        response = await insert_handler(request=request, user=user)
        
        assert isinstance(response, InsertArticlesResponse)
        assert response.processed == service_result["processed"]
        assert response.created == service_result["created"]
        assert response.updated == service_result["updated"]
        assert response.skipped == service_result["skipped"]
        
        mock_pubmed_service.insert_articles_by_keyword.assert_called_once_with(
            keyword=keyword,
            created_by=user,
            pubmed_db=pubmed_db
        )

    @pytest.mark.parametrize("service_error,expected_status", [
        (ValueError("Invalid keyword format"), 500),
        (RuntimeError("Database connection failed"), 500),
        (Exception("Service temporarily unavailable"), 500),
        (ConnectionError("Network timeout"), 500),
    ])
    @pytest.mark.asyncio
    async def test_insert_articles_service_errors(self, pubmed_router, mock_pubmed_service, service_error, expected_status):
        mock_pubmed_service.insert_articles_by_keyword.side_effect = service_error
        
        request = InsertArticlesRequest(keyword="test", pubmed_db="pubmed")
        
        insert_handler = None
        for route in pubmed_router.router.routes:
            if route.path == "/pubmed/articles" and "POST" in route.methods:
                insert_handler = route.endpoint
                break
        
        with pytest.raises(HTTPException) as exc_info:
            await insert_handler(request=request, user="test_user")
        
        assert exc_info.value.status_code == expected_status
        assert str(service_error) == str(exc_info.value.detail)

    @pytest.mark.parametrize("keyword", [
        ("ga4gh"),
        ("ga4gh beacon"),
        ("ga4gh REWS"),
        ("ga4gh DRS"),
    ])
    @pytest.mark.asyncio
    async def test_get_articles_basic_keyword_search(self, pubmed_router, mock_pubmed_service, sample_articles, keyword):
        mock_pubmed_service.get_articles_by_keyword.return_value = sample_articles
        
        handler = None
        for route in pubmed_router.router.routes:
            if route.path == "/pubmed/articles/{keyword}" and "GET" in route.methods:
                handler = route.endpoint
                break
        
        assert handler is not None
        
        result = await handler(keyword=keyword, start_date=None, end_date=None, status=None)
        
        assert result == sample_articles
        assert len(result) == len(sample_articles)
        
        assert mock_pubmed_service.get_articles_by_keyword.call_count == 1
        mock_pubmed_service.get_articles_by_keyword.assert_called_with(keyword=keyword)
        
        mock_pubmed_service.get_articles_by_keyword_and_date.assert_not_called()
        mock_pubmed_service.get_articles_by_keyword_and_status.assert_not_called()

    @pytest.mark.parametrize("keyword,start_date,end_date", [
        ("ga4gh", datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC)),
        ("ga4gh", datetime(2023, 1, 1, tzinfo=UTC), datetime(2023, 12, 31, tzinfo=UTC)),
        ("ga4gh", datetime(2020, 11, 11, tzinfo=UTC), None),
        ("ga4gh", datetime(2020, 1, 1, tzinfo=UTC), datetime(2025, 1, 1, tzinfo=UTC)),
    ])
    @pytest.mark.asyncio
    async def test_get_articles_date_filtering(self, pubmed_router, mock_pubmed_service, sample_articles, keyword, start_date, end_date):
        mock_pubmed_service.get_articles_by_keyword_and_date.return_value = sample_articles
        
        handler = None
        for route in pubmed_router.router.routes:
            if route.path == "/pubmed/articles/{keyword}" and "GET" in route.methods:
                handler = route.endpoint
                break
        
        result = await handler(keyword=keyword, start_date=start_date, end_date=end_date, status=None)
        
        assert result == sample_articles
        
        call_args = mock_pubmed_service.get_articles_by_keyword_and_date.call_args
        assert call_args[1]["keyword"] == keyword
        assert call_args[1]["start_date"] == start_date
        
        if end_date is None:
            assert call_args[1]["end_date"] is not None
            assert call_args[1]["end_date"] <= datetime.now(tz=UTC)
        else:
            assert call_args[1]["end_date"] == end_date
        
        mock_pubmed_service.get_articles_by_keyword.assert_not_called()
        mock_pubmed_service.get_articles_by_keyword_and_status.assert_not_called()

    @pytest.mark.parametrize("keyword,status", [
        ("ga4gh", "published"),
        ("ga4gh", "preprint"),
        ("ga4gh", "redacted"),
        ("ga4gh", "update"),
        ("ga4gh", "unknown"),
    ])
    @pytest.mark.asyncio
    async def test_get_articles_status_filtering(self, pubmed_router, mock_pubmed_service, sample_articles, keyword, status):
        mock_pubmed_service.get_articles_by_keyword_and_status.return_value = sample_articles
        
        handler = None
        for route in pubmed_router.router.routes:
            if route.path == "/pubmed/articles/{keyword}" and "GET" in route.methods:
                handler = route.endpoint
                break
        
        result = await handler(keyword=keyword, start_date=None, end_date=None, status=status)
        
        assert result == sample_articles
        
        mock_pubmed_service.get_articles_by_keyword_and_status.assert_called_once_with(
            keyword=keyword,
            status=status
        )
        
        mock_pubmed_service.get_articles_by_keyword.assert_not_called()
        mock_pubmed_service.get_articles_by_keyword_and_date.assert_not_called()

    @pytest.mark.parametrize("start_date,end_date", [
        (datetime(2025, 12, 31, tzinfo=UTC), datetime(2025, 1, 1, tzinfo=UTC)), 
        (datetime(2025, 6, 1, tzinfo=UTC), datetime(2025, 6, 1, tzinfo=UTC)),
        (datetime(2025, 12, 1, tzinfo=UTC), datetime(2025, 11, 1, tzinfo=UTC)),
    ])
    @pytest.mark.asyncio
    async def test_get_articles_invalid_date_range(self, pubmed_router, mock_pubmed_service, start_date, end_date):
        handler = None
        for route in pubmed_router.router.routes:
            if route.path == "/pubmed/articles/{keyword}" and "GET" in route.methods:
                handler = route.endpoint
                break
        
        with pytest.raises(HTTPException) as exc_info:
            await handler(keyword="test", start_date=start_date, end_date=end_date, status=None)
        
        assert exc_info.value.status_code == 500
        assert "Start date must be before end date" in exc_info.value.detail
        
        mock_pubmed_service.get_articles_by_keyword_and_date.assert_not_called()
        mock_pubmed_service.get_articles_by_keyword.assert_not_called()
        mock_pubmed_service.get_articles_by_keyword_and_status.assert_not_called()

    @pytest.mark.parametrize("search_params,service_method", [
        ({"start_date": None, "end_date": None, "status": None}, "get_articles_by_keyword"),
        ({"start_date": datetime(2025, 1, 1, tzinfo=UTC), "end_date": None, "status": None}, "get_articles_by_keyword_and_date"),
        ({"start_date": None, "end_date": None, "status": "published"}, "get_articles_by_keyword_and_status"),
    ])
    @pytest.mark.asyncio
    async def test_get_articles_no_results_found(self, pubmed_router, mock_pubmed_service, search_params, service_method):
        getattr(mock_pubmed_service, service_method).return_value = []
        
        handler = None
        for route in pubmed_router.router.routes:
            if route.path == "/pubmed/articles/{keyword}" and "GET" in route.methods:
                handler = route.endpoint
                break
        
        with pytest.raises(HTTPException) as exc_info:
            await handler(keyword="nonexistent", **search_params)
        
        assert exc_info.value.status_code == 500
        assert "No articles found for criteria" in exc_info.value.detail

    @pytest.mark.parametrize("service_method,service_error", [
        ("get_articles_by_keyword", ValueError("Invalid keyword")),
        ("get_articles_by_keyword_and_date", RuntimeError("Database error")),
        ("get_articles_by_keyword_and_status", ConnectionError("Service unavailable")),
    ])
    @pytest.mark.asyncio
    async def test_get_articles_service_errors(self, pubmed_router, mock_pubmed_service, service_method, service_error):
        getattr(mock_pubmed_service, service_method).side_effect = service_error
        
        handler = None
        for route in pubmed_router.router.routes:
            if route.path == "/pubmed/articles/{keyword}" and "GET" in route.methods:
                handler = route.endpoint
                break
        
        params = {"start_date": None, "end_date": None, "status": None}
        if "date" in service_method:
            params["start_date"] = datetime(2025, 1, 1, tzinfo=UTC)
        elif "status" in service_method:
            params["status"] = "published"
        
        with pytest.raises(HTTPException) as exc_info:
            await handler(keyword="test", **params)
        
        assert exc_info.value.status_code == 500
        assert str(service_error) in str(exc_info.value.detail)