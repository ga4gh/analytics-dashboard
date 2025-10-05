from datetime import datetime

from src.models.article import Article as ArticleModel

from .setup import DatabaseConnection
from .sqlbuilder import SQLBuilder


class Article:
    def __init__(self, db: DatabaseConnection, sql_builder: SQLBuilder) -> None:
        self.db = db
        self.sql_builder = sql_builder

    def insert(self, article: ArticleModel) -> int:
        data = article.model_dump(exclude={"id", "authors"})
        query, values = self.sql_builder.build_insert(data)

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, values)
                article_id = cur.fetchone()[0]
                conn.commit()
                return article_id

    def update(self, article: ArticleModel) -> None:
        data = article.model_dump(exclude={"id", "authors"})
        query, values = self.sql_builder.build_update(data, article.id, "id")

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def get_by_id(self, article_id: int) -> ArticleModel | None:
        query = "SELECT * FROM articles WHERE id = %s"

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, (article_id,))
                row = cur.fetchone()

                if row and cur.description:
                    columns = [desc[0] for desc in cur.description]
                    data = dict(zip(columns, row, strict=False))
                    return ArticleModel(**data)
                return None

    def get_by_source_id(self, source_id: str) -> ArticleModel | None:
        query = "SELECT * FROM articles WHERE source_id = %s"

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, (source_id,))
                row = cur.fetchone()

                if row and cur.description:
                    columns = [desc[0] for desc in cur.description]
                    data = dict(zip(columns, row, strict=False))
                    return ArticleModel(**data)
                return None

    def get_by_keyword(self, keyword: str) -> list[ArticleModel]:
        query = """
            SELECT a.* FROM articles a
            JOIN records r ON a.record_id = r.id
            WHERE %s = ANY(r.keyword)
        """

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, (keyword,))
                rows = cur.fetchall()

                articles = []
                if rows and cur.description:
                    columns = [desc[0] for desc in cur.description]
                    for row in rows:
                        data = dict(zip(columns, row, strict=False))
                        articles.append(ArticleModel(**data))
                return articles

    def get_by_keyword_and_date(self, keyword: str, start_date: datetime, end_date: datetime) -> list[ArticleModel]:
        query = """
            SELECT a.* FROM articles a
            JOIN records r ON a.record_id = r.id
            WHERE %s = ANY(r.keyword) AND a.publish_date BETWEEN %s AND %s
        """

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, (keyword, start_date, end_date))
                rows = cur.fetchall()

                articles = []
                if rows and cur.description:
                    columns = [desc[0] for desc in cur.description]
                    for row in rows:
                        data = dict(zip(columns, row, strict=False))
                        articles.append(ArticleModel(**data))
                return articles

    def get_by_keyword_and_status(self, keyword: str, status: str) -> list[ArticleModel]:
        query = """
            SELECT a.* FROM articles a
            JOIN records r ON a.record_id = r.id
            WHERE %s = ANY(r.keyword) AND a.status = %s
        """

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, (keyword, status))
                rows = cur.fetchall()

                articles = []
                if rows and cur.description:
                    columns = [desc[0] for desc in cur.description]
                    for row in rows:
                        data = dict(zip(columns, row, strict=False))
                        articles.append(ArticleModel(**data))
                return articles
