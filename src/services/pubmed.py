from datetime import UTC, datetime

import requests

from src.clients.pubmed import Pubmed as PubmedClient
from src.models.article import Article
from src.models.article import Status as ArticleStatus
from src.models.author import ArticleType
from src.models.record import Record, RecordType, Source, Status
from src.repositories.article import Article as ArticleRepository
from src.repositories.author import Author as AuthorRepository
from src.repositories.record import Record as RecordRepository


class Pubmed:
    def __init__(
        self,
        author_repo: AuthorRepository,
        record_repo: RecordRepository,
        article_repo: ArticleRepository,
        pubmed_client: PubmedClient
    ) -> None:
        self.author_repo = author_repo
        self.record_repo = record_repo
        self.article_repo = article_repo
        self.pubmed_client = pubmed_client

    def insert_articles_by_keyword(self, keyword: str, created_by: str,
                                   pubmed_db: str) -> dict[str, int]:
        processed = 0
        created = 0
        updated = 0
        skipped = 0

        uids = self.pubmed_client.get_uids(db=pubmed_db, term=keyword)
        if not uids:
            return {
                "processed": 0,
                "created": 0,
                "updated": 0,
                "skipped": 0
            }

        articles = self.pubmed_client.get_article_summaries(db=pubmed_db, ids=uids)

        for article in articles:
            processed += 1
            existing_article = self.article_repo.get_by_source_id(article.source_id)

            if existing_article is not None:
                existing_record = self.record_repo.get_by_id(existing_article.record_id)
                if existing_record.keyword is None:
                    existing_record.keyword = [keyword]
                    existing_record.updated_by = created_by
                    existing_record.updated_at = datetime.now(UTC)
                    existing_record.version += 1

                    self.record_repo.update(existing_record)
                    updated += 1

                elif keyword not in existing_record.keyword:
                    existing_record.keyword.append(keyword)
                    existing_record.updated_by = created_by
                    existing_record.updated_at = datetime.now(UTC)
                    existing_record.version += 1

                    self.record_repo.update(existing_record)
                    updated += 1
            else:
                try:
                    detailed_article, status = self.pubmed_client.get_detailed_article_info(db=pubmed_db,
                                                                                     article_id=article.source_id)

                    if detailed_article:
                        article.abstract = detailed_article.abstract
                        article.status = self._normalize_pubmed_status(status, article.journal)
                        article.link = detailed_article.link

                        record = Record(
                            record_type=RecordType.ARTICLE,
                            source=Source.PUBMED,
                            status=Status.PENDING,
                            keyword=[keyword],
                            product_line=None,
                            created_by=created_by,
                            updated_by=created_by
                        )
                        record_id = self.record_repo.insert(record)
                        article.record_id = record_id

                        article.created_by = created_by
                        article.updated_by = created_by

                        article_id = self.article_repo.insert(article)

                        if detailed_article.authors:
                            for author_data in detailed_article.authors:
                                author_data.article_id = article_id
                                author_data.article_type = ArticleType.ARTICLE
                                author_data.created_by = created_by
                                author_data.updated_by = created_by

                                self.author_repo.insert(author_data)

                        created += 1
                    else:
                        skipped += 1
                except (requests.RequestException, ValueError, KeyError):
                    skipped += 1

        return {
            "processed": processed,
            "created": created,
            "updated": updated,
            "skipped": skipped
        }

    def get_articles_by_keyword(self, keyword: str) -> list[Article]:
        articles = self.article_repo.get_by_keyword(keyword)

        for article in articles:
            if article.id:
                authors = self.author_repo.get_by_article_id(article.id)
                article.authors = authors

        return articles

    def get_articles_by_keyword_and_date(self, keyword: str, start_date: datetime, end_date: datetime) -> list[Article]:
        articles = self.article_repo.get_by_keyword_and_date(keyword, start_date, end_date)

        for article in articles:
            if article.id:
                authors = self.author_repo.get_by_article_id(article.id)
                article.authors = authors

        return articles

    def get_articles_by_keyword_and_status(self, keyword: str, status: str) -> list[Article]:
        articles = self.article_repo.get_by_keyword_and_status(keyword, status)

        for article in articles:
            if article.id:
                authors = self.author_repo.get_by_article_id(article.id)
                article.authors = authors

        return articles

    def _normalize_pubmed_status(self, pubmed_status: str, journal: str) -> ArticleStatus: # noqa: PLR0911
        if not pubmed_status:
            return ArticleStatus.UNKNOWN

        status_lower = pubmed_status.lower().strip()

        preprint_statuses = {
            "aheadofprint", "preprint", "epub ahead of print", "online ahead of print",
            "ahead of print", "in press", "accepted", "received", "revised"
        }

        if status_lower in preprint_statuses or "xiv" in journal.lower():
            return ArticleStatus.PREPRINT

        published_statuses = {
            "ppublish", "epublish", "entrez", "pubmed", "medline", "pmc", "pmc-release"
        }

        if status_lower in published_statuses:
            return ArticleStatus.PUBLISHED

        redacted_statuses = {
            "retracted", "in-error", "corrected", "withdrawn", "redacted",
            "erratum", "corrigendum", "expression of concern", "retraction",
            "partial retraction", "duplicate publication"
        }

        if status_lower in redacted_statuses:
            return ArticleStatus.REDACTED

        preprint_servers = [
            "biorxiv", "medrxiv", "arxiv", "chemrxiv", "psyarxiv",
            "socarxiv", "eartharxiv", "preprint"
        ]

        if any(server in status_lower for server in preprint_servers):
            return ArticleStatus.PREPRINT

        correction_terms = [
            "correction", "update", "addendum", "publisher corrected",
            "author corrected", "republished"
        ]

        if any(term in status_lower for term in correction_terms):
            return ArticleStatus.UPDATED

        return ArticleStatus.UNKNOWN
