from datetime import datetime

from src.models.pmc_article import PMCArticleFull as ArticleModel
from src.models.entities.pmc_article import PMCArticle
from .setup import DatabaseConnection
from .sqlbuilder import SQLBuilder
import json
from typing import List
from sqlalchemy.orm import Session, selectinload


class EPMCRepo:
    '''def __init__(self, db: DatabaseConnection, sql_builder: SQLBuilder) -> None:
        self.db = db
        self.sql_builder = sql_builder
    '''
    
    def __init__(self, db: Session):
        self.db = db
    
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
        query = "SELECT * FROM pmc_articles WHERE id = %s"

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, (article_id,))
                row = cur.fetchone()

                if row and cur.description:
                    columns = [desc[0] for desc in cur.description]
                    data = dict(zip(columns, row, strict=False))
                    return ArticleModel(**data)
                return None

    def get_by_source_id(self, source_id: str) -> ArticleModel | None:
        query = "SELECT * FROM pmc_articles WHERE source_id = %s"

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
            SELECT a.* FROM pmc_articles a
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
            SELECT a.* FROM pmc_articles a
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
            SELECT a.* FROM pmc_articles a
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
        
def get_all_articles_old(self) -> list[ArticleModel]:
    query = """
    SELECT jsonb_build_object(
        'id', a.id,
        'record_id', a.record_id,
        'source', a.source,
        'pm_id', a.pm_id,
        'pmc_id', a.pmc_id,
        'full_text_id', a.full_text_id,
        'doi', a.doi,
        'title', a.title,
        'pub_year', a.pub_year,
        'abstract_text', a.abstract_text,
        'affiliation', a.affiliation,
        'publicication_status', a.publicication_status,
        'language', a.language,
        'pub_type', a.pub_type,
        'is_open_access', a.is_open_access,
        'inEPMC', a."inEPMC",
        'inPMC', a."inPMC",
        'has_PDF', a."has_PDF",
        'has_Book', a."has_Book",
        'has_Suppl', a."has_Suppl",
        'cited_by_count', a.cited_by_count,
        'has_references', a.has_references,
        'date_of_creation', a.date_of_creation,
        'first_index_date', a.first_index_date,
        'fulltext_receive_date', a.fulltext_receive_date,
        'revision_date', a.revision_date,
        'epub_date', a.epub_date,
        'first_publication_date', a.first_publication_date,

        'authors', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                'id', au.id,
                'fullname', au.fullname,
                'firstname', au.firstname,
                'lastname', au.lastname,
                'initials', au.initials,
                'orcid', au.orcid,
                'author_order', aa.author_order
            ) ORDER BY aa.seq_id)
            FROM articles_authors aa
            JOIN authors au ON au.id = aa.author_id
            WHERE aa.article_id = a.id
        ), '[]'),

        'affiliations', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                'id', af.id,
                'author_id', af.author_id,
                'org_name', af.org_name,
                'article_id', af.article_id,
                'affiliation_order', af.affiliation_order
            ) ORDER BY af.seq_id)
            FROM affiliations af
            WHERE af.article_id = a.id
        ), '[]'),

        'keywords', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                'id', k.id,
                'value', k.value
            ))
            FROM keywords k
            WHERE k.article_id = a.id
        ), '[]'),

        'grants', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                'id', g.id,
                'grant_id', g.grant_id,
                'agency', g.agency
            ))
            FROM grants g
            WHERE g.article_id = a.id
        ), '[]'),

        'fulltexts', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                'id', f.id,
                'availibility', f.availibility,
                'availibility_code', f.availibility_code,
                'document_style', f.document_style,
                'site', f.site,
                'url', f.url
            ))
            FROM fulltexts f
            WHERE f.article_id = a.id
        ), '[]'),

        'citations', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                'id', c.id,
                'citation_id', c.citation_id,
                'source', c.source,
                'citation_type', c.citation_type,
                'title', c.title,
                'authors', c.authors,
                'pub_year', c.pub_year,
                'citation_count', c.citation_count
            ))
            FROM citations c
            WHERE c.article_id = a.id
        ), '[]'),

        'references', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                'id', r.id,
                'reference_id', r.reference_id,
                'source', r.source,
                'citation_type', r.citation_type,
                'title', r.title,
                'authors', r.authors,
                'pub_year', r.pub_year,
                'ISSN', r."ISSN",
                'ESSN', r."ESSN",
                'cited_order', r.cited_order,
                'match', r.match
            ) ORDER BY r.cited_order)
            FROM "references" r
            WHERE r.article_id = a.id
        ), '[]')
    )
    FROM pmc_articles a;
    """

    with self.db.get_connection() as conn, conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    return [ArticleModel.model_validate(row[0]) for row in rows]

def get_all_articles(self) -> list[PMCArticle]:
        """
        Fetch all articles with all child relationships loaded.
        """
        return (
            self.db.query(PMCArticle)
            .options(
                selectinload(PMCArticle.article_authors),
                selectinload(PMCArticle.affiliations),
                selectinload(PMCArticle.keywords),
                selectinload(PMCArticle.grants),
                selectinload(PMCArticle.fulltexts),
                selectinload(PMCArticle.citations),
                selectinload(PMCArticle.references),
            )
            .all()
        )

