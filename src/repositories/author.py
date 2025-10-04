from src.models.author import Author as AuthorModel

from .setup import DatabaseConnection
from .sqlbuilder import SQLBuilder


class Author:
    def __init__(self, db: DatabaseConnection, sql_builder: SQLBuilder) -> None:
        self.db = db
        self.sql_builder = sql_builder

    def insert(self, author: AuthorModel) -> None:
        data = author.model_dump(exclude={"id", "affiliations"})
        query, values = self.sql_builder.build_insert(data)

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def update(self, author: AuthorModel) -> None:
        data = author.model_dump(exclude={"id", "affiliations"})
        query, values = self.sql_builder.build_update(data, author.id, "id")

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def get_by_id(self, id: int) -> AuthorModel | None:
        query = "SELECT * FROM authors WHERE id = %s"

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, (id,))
                row = cur.fetchone()

                if row and cur.description:
                    columns = [desc[0] for desc in cur.description]
                    data = dict(zip(columns, row, strict=False))
                    return AuthorModel(**data)
                return None

    def get_by_article_id(self, article_id: int) -> list[AuthorModel]:
        query = "SELECT * FROM authors WHERE article_id = %s"

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, (article_id,))
                rows = cur.fetchall()

                authors = []
                if rows and cur.description:
                    columns = [desc[0] for desc in cur.description]
                    for row in rows:
                        data = dict(zip(columns, row, strict=False))
                        authors.append(AuthorModel(**data))
                return authors