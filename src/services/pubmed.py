from datetime import datetime, timezone
from typing import Dict, List
from src.clients.pubmed import Pubmed as PubmedClient
from src.repositories.article import Article as ArticleRepository
from src.repositories.record import Record as RecordRepository
from src.repositories.author import Author as AuthorRepository
from src.models.article import Article, Status
from src.models.record import Record, RecordType, Source, Status, ProductType
from src.models.author import ArticleType

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
    
    def insert_articles_by_keyword(self, keyword: str, created_by: str, pubmed_db: str) -> Dict[str, int]:
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
                    existing_record.updated_at = datetime.now(timezone.utc)
                    existing_record.version += 1

                    self.record_repo.update(existing_record)
                    updated += 1

                elif keyword not in existing_record.keyword:
                    existing_record.keyword.append(keyword)
                    existing_record.updated_by = created_by
                    existing_record.updated_at = datetime.now(timezone.utc)
                    existing_record.version += 1

                    self.record_repo.update(existing_record)
                    updated += 1
            else:
                try:
                    detailed_article = self.pubmed_client.get_detailed_article_info(db=pubmed_db, id=article.source_id)
                    
                    if detailed_article:
                        article.abstract = detailed_article.abstract
                        article.status = detailed_article.status
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
                except Exception as e:
                    print(f"Error processing article {article.source_id}: {e}")
                    skipped += 1
                
        return {
            "processed": processed,
            "created": created,
            "updated": updated,
            "skipped": skipped
        }

    def get_articles_by_keyword(self, keyword: str) -> List[Article]:
        articles = self.article_repo.get_by_keyword(keyword)
        
        for article in articles:
            if article.id:
                authors = self.author_repo.get_by_article_id(article.id)
                article.authors = authors
        
        return articles

    def get_articles_by_keyword_and_date(self, keyword: str, start_date: datetime, end_date: datetime) -> List[Article]:
        articles = self.article_repo.get_by_keyword_and_date(keyword, start_date, end_date)
        
        for article in articles:
            if article.id:
                authors = self.author_repo.get_by_article_id(article.id)
                article.authors = authors
        
        return articles

    def get_articles_by_keyword_and_status(self, keyword: str, status: str) -> List[Article]:
        articles = self.article_repo.get_by_keyword_and_status(keyword, status)
        
        for article in articles:
            if article.id:
                authors = self.author_repo.get_by_article_id(article.id)
                article.authors = authors
        
        return articles