from datetime import datetime
from typing import Any, Optional, Type, List

from src.models.entities.pmc_article import PMCArticle

import json

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
    
    def __init__(self, db: Session):
        
        self.db = db
    
    def insert(self, entity: Any, entity_cls: Type[PMCArticle] = PMCArticle) -> int:
        # CHANGE: ORM-only insert. Expect an ORM entity instance.
        # Reason: Client now returns ORM objects; we no longer handle Pydantic dict conversion.
        if not isinstance(entity, entity_cls):
            raise TypeError(f"Expected instance of {entity_cls.__name__}, got {type(entity).__name__}")
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity.id

    def update(self, entity: Any, entity_cls: Type[PMCArticle] = PMCArticle) -> Optional[int]:
        # CHANGE: ORM-only update. Merge the given entity and commit.
        if not isinstance(entity, entity_cls):
            raise TypeError(f"Expected instance of {entity_cls.__name__}, got {type(entity).__name__}")
        merged = self.db.merge(entity)
        self.db.commit()
        return getattr(merged, "id", None)

    def get_by_id(self, entity_id: int, entity_cls: Type[PMCArticle] = PMCArticle):
        # CHANGE: Return ORM entity (no Pydantic validation).
        return self.db.get(entity_cls, entity_id)

    def get_by_source_id(self, source_id: str, entity_cls: Type[PMCArticle] = PMCArticle):
        # CHANGE: Use pm_id or pmc_id (PMCArticle has no source_id column).
        id_column = getattr(entity_cls, "pm_id", getattr(entity_cls, "pmc_id", None))
        if id_column is None:
            raise AttributeError(f"{entity_cls.__name__} has no 'pm_id' or 'pmc_id' column")
        return (
            self.db.query(entity_cls)
            .filter(id_column == source_id)
            .first()
        )

    def get_by_author_name(self, fullname: str, firstname: str, lastname: str) -> PMCAuthor | None:
        return (
            self.db.query(PMCAuthor)
            .join(ArticleAuthor, ArticleAuthor.author_id == PMCAuthor.id)
            # Optional: require association to an article (but DON'T join PMCAuthor again)
            .join(PMCArticle, PMCArticle.id == ArticleAuthor.article_id)
            .filter(
                PMCAuthor.fullname == fullname,
                PMCAuthor.firstname == firstname,
                PMCAuthor.lastname == lastname,
            )
            .first()
        )

    def get_by_keyword(self, keyword: str, entity_cls: Type[PMCArticle] = PMCArticle) -> list:
        # CHANGE: Keyword.value is a PostgreSQL ARRAY(String); use .any(keyword) to emulate '= ANY(array)'.
        return (
            self.db.query(entity_cls)
            .join(Keyword, Keyword.article_id == entity_cls.id)
            .filter(Keyword.value.any(keyword))
            .all()
        )

    def get_by_keyword_and_date(
        self,
        keyword: str,
        start_date: datetime,
        end_date: datetime,
        entity_cls: Type[PMCArticle] = PMCArticle,
    ) -> list:
        # CHANGE: Use a real date column; PMCArticle has 'first_publication_date'.
        # If your entity uses a different date field, update here.
        date_column = getattr(entity_cls, "first_publication_date", None)
        if date_column is None:
            date_column = getattr(entity_cls, "date_of_creation")  # fallback
        return (
            self.db.query(entity_cls)
            .join(Keyword, Keyword.article_id == entity_cls.id)
            .filter(
                Keyword.value.any(keyword),
                date_column.between(start_date, end_date),
            )
            .all()
        )

    def get_by_keyword_and_status(
        self,
        keyword: str,
        status: str,
        entity_cls: Type[PMCArticle] = PMCArticle,
    ) -> list:
        # CHANGE: PMCArticle uses 'publication_status'. Fallback to 'status' if present for other entities.
        status_column = getattr(entity_cls, "publication_status", getattr(entity_cls, "status", None))
        if status_column is None:
            raise AttributeError(f"{entity_cls.__name__} has no 'publication_status' or 'status' column")
        return (
            self.db.query(entity_cls)
            .join(Keyword, Keyword.article_id == entity_cls.id)
            .filter(
                Keyword.value.any(keyword),
                status_column == status,
            )
            .all()
        )

    def insert_or_update(self, entity, type, update: bool):
        if update:
            entity_id = self.update(entity, type)
        else:
            entity_id = self.insert(entity, type)
        return entity_id

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

def get_all_articles_old(self) -> list[PMCArticle]:
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
        'has_Suppl", a."has_Suppl",
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

    return [PMCArticle.model_validate(row[0]) for row in rows]

