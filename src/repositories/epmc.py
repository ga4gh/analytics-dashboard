from datetime import datetime

from src.models.pmc_article import PMCArticleFull as ArticleModel
from src.models.entities.pmc_article import PMCArticle
from .setup import DatabaseConnection
from .sqlbuilder import SQLBuilder
import json
from typing import List, Optional, Type
from sqlalchemy.orm import Session, selectinload

# Reusable ORM entities for cross-table queries
from src.models.entities.pmc_author import PMCAuthor, ArticleAuthor
from src.models.entities.extras import Keyword
from src.models.entities.citations import Citation, Reference


class EPMCRepo:
    '''def __init__(self, db: DatabaseConnection, sql_builder: SQLBuilder) -> None:
        self.db = db
        self.sql_builder = sql_builder
    '''
    
    def __init__(self, db: Session, entity_cls: Type[PMCArticle] = PMCArticle, model_cls: Type[ArticleModel] = ArticleModel):
        # Allow re-use across tables by passing a different SQLAlchemy entity class and corresponding Pydantic model
        self.db = db
        self.entity_cls = entity_cls
        self.model_cls = model_cls
    
    def insert(self, article: ArticleModel) -> int:
        # SQLAlchemy ORM insert: create an entity instance from the Pydantic model, excluding non-column fields
        # Build exclude set dynamically: anything on the Pydantic model that is not an attribute on the ORM entity
        exclude_fields = {name for name in article.__class__.model_fields.keys() if not hasattr(self.entity_cls, name)}
        exclude_fields.add("id")  # let DB autogenerate PK

        data = article.model_dump(exclude=exclude_fields)
        # Keep only fields that are mapped columns on the entity
        filtered = {k: v for k, v in data.items() if hasattr(self.entity_cls, k)}

        obj = self.entity_cls(**filtered)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj.id

    def update(self, article: ArticleModel) -> None:
        # SQLAlchemy ORM update: fetch the row and set attributes from the Pydantic model
        db_obj = self.db.get(self.entity_cls, article.id)
        if not db_obj:
            return

        exclude_fields = {name for name in article.__class__.model_fields.keys() if not hasattr(self.entity_cls, name)}
        exclude_fields.add("id")

        data = article.model_dump(exclude=exclude_fields)
        for k, v in data.items():
            if hasattr(self.entity_cls, k):
                setattr(db_obj, k, v)

        self.db.commit()

    def get_by_id(self, article_id: int) -> ArticleModel | None:
        # ORM lookup by primary key on the configured entity class
        db_obj = self.db.get(self.entity_cls, article_id)
        return self.model_cls.model_validate(db_obj) if db_obj else None

    def get_by_source_id(self, source_id: str) -> ArticleModel | None:
        # ORM query by source/source_id; choose whichever column exists on the entity
        # If your entity uses `source` instead of `source_id`, this will gracefully use `source`
        source_column = getattr(self.entity_cls, "source_id", getattr(self.entity_cls, "source", None))
        if source_column is None:
            # comment: set the correct column name here if neither source_id nor source exists on your entity
            raise AttributeError(f"{self.entity_cls.__name__} has no 'source_id' or 'source' column")

        db_obj = (
            self.db.query(self.entity_cls)
            .filter(source_column == source_id)
            .first()
        )
        return self.model_cls.model_validate(db_obj) if db_obj else None

    def get_by_author_name(self, fullname: str, firstname: str, lastname: str) -> ArticleModel | None:
        # ORM query joining authors to articles via the association table
        # NOTE: This assumes self.entity_cls == PMCArticle; for other entities, adjust joins accordingly.
        db_obj = (
            self.db.query(self.entity_cls)
            .join(ArticleAuthor, ArticleAuthor.article_id == PMCArticle.id)
            .join(PMCAuthor, PMCAuthor.id == ArticleAuthor.author_id)
            .filter(
                PMCAuthor.fullname == fullname,
                PMCAuthor.firstname == firstname,
                PMCAuthor.lastname == lastname,
            )
            .first()
        )
        return self.model_cls.model_validate(db_obj) if db_obj else None

    def get_by_keyword(self, keyword: str) -> list[ArticleModel]:
        # ORM query joining Keyword relationship and filtering on PostgreSQL ARRAY column
        # WHERE %s = ANY(r.keyword) → Keyword.value.any(keyword)
        rows = (
            self.db.query(self.entity_cls)
            .join(Keyword, Keyword.article_id == PMCArticle.id)
            .filter(Keyword.value.any(keyword))
            .all()
        )
        return [self.model_cls.model_validate(row) for row in rows]

    def get_by_keyword_and_date(self, keyword: str, start_date: datetime, end_date: datetime) -> list[ArticleModel]:
        # ORM query by keyword and date range; choose the correct date column on the entity
        # Default to PMCArticle.first_publication_date (adjust if your entity uses a different date field)
        date_column = getattr(self.entity_cls, "first_publication_date", None)
        if date_column is None:
            # comment: set to the correct date column (e.g., self.entity_cls.publish_date) if different
            raise AttributeError(f"{self.entity_cls.__name__} has no 'first_publication_date' column")

        rows = (
            self.db.query(self.entity_cls)
            .join(Keyword, Keyword.article_id == PMCArticle.id)
            .filter(
                Keyword.value.any(keyword),
                date_column.between(start_date, end_date),
            )
            .all()
        )
        return [self.model_cls.model_validate(row) for row in rows]

    def get_by_keyword_and_status(self, keyword: str, status: str) -> list[ArticleModel]:
        # ORM query by keyword and publication status; identify the right status column
        status_column = getattr(self.entity_cls, "publication_status", None)
        if status_column is None:
            # comment: set to the correct status column (e.g., self.entity_cls.status) if your entity differs
            raise AttributeError(f"{self.entity_cls.__name__} has no 'publication_status' column")

        rows = (
            self.db.query(self.entity_cls)
            .join(Keyword, Keyword.article_id == PMCArticle.id)
            .filter(
                Keyword.value.any(keyword),
                status_column == status,
            )
            .all()
        )
        return [self.model_cls.model_validate(row) for row in rows]
        
        
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

