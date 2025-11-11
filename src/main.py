import uvicorn
from fastapi import FastAPI

from .clients import pubmed
from .config import constants
from .config.config import config
from .models.article import Article
from .models.author import Author
from .models.record import Record
from .repositories import setup, sqlbuilder
from .repositories.article import Article as ArticleRepo
from .repositories.author import Author as AuthorRepo
from .repositories.record import Record as RecordRepo
from .routers.pubmed import Pubmed as PubmedRouter
from .services.pubmed import Pubmed as PubmedService


def main() -> FastAPI:

    # DB setup
    db_conn = setup.DatabaseConnection(config.database_url)
    db_conn.connect()

    record_fields = set(Record.model_fields.keys())
    record_sql_builder = sqlbuilder.SQLBuilder("records").allow_fields(record_fields - {"id"})
    record_repo = RecordRepo(db_conn, record_sql_builder)

    article_fields = set(Article.model_fields.keys())
    article_sql_builder = sqlbuilder.SQLBuilder("articles").allow_fields(article_fields - {"id"})
    article_repo = ArticleRepo(db_conn, article_sql_builder)

    author_fields = set(Author.model_fields.keys())
    author_sql_builder = sqlbuilder.SQLBuilder("authors").allow_fields(author_fields - {"id"})
    author_repo = AuthorRepo(db_conn, author_sql_builder)

    # Client setup
    pubmed_client = pubmed.Pubmed(constants.PUBMED_BASE_URL, config.pubmed_api_key)

    # Service setup
    pubmed_service = PubmedService(author_repo, record_repo, article_repo, pubmed_client)

    # Router setup
    pubmed_router = PubmedRouter(pubmed_service)

    app = FastAPI()
    app.include_router(pubmed_router.router)

    return app

if __name__ == "__main__":
    app = main()
    uvicorn.run(app, host=config.host, port=config.port, reload=False)
