from typing import List
from unittest import skip

from src.clients.epmc import EPMCClient

from src.models.citation import CitationsOverYears
from src.models.entities.pmc_article import PMCArticle
from src.models.entities.pmc_author import PMCAuthor, PMCAffiliation, ArticleAuthor
from src.models.entities.extras import Grant, FullText, Keyword
from src.models.entities.citations import Citation, Reference
from src.models.entities.record import Record, RecordType, Source, Status, ProductType
from src.models.entities.ingestion import Ingestion

from src.repositories.epmc import EPMCRepo

#from src.services.grant import Grant


class EPMCService:
    def __init__(self, repo: EPMCRepo) -> None:
        self.epmc_repo = repo
        self.epmc_client = EPMCClient()
        # Defer heavy DB loads to avoid blocking startup. These maps will be
        # populated on first use by calling the loader helpers.
        self.articles_records: dict[str, int] = {}
        self.highest_versions_by_source_id: dict[str, int] = {}
        self.ingested_articles: dict[int, int] = {}
        try:
            self.highest_ingestion_version = repo.get_highest_ingestion_version()
        except Exception:
            self.highest_ingestion_version = 0
        self.ingestion_id = None

    def _load_articles_records(self) -> dict[str, int]:
        article_rows = self.epmc_repo.get_all_articles_ids()
        return {
            pm_id: record_id
            for pm_id, record_id in article_rows
            if pm_id is not None
        }
    
    def _load_versions_by_source_id(self) -> dict[str, int]:
        return self.epmc_repo.get_max_version_by_source_id()

    def list_fulltext_keys(self) -> list[str]:
        """Return all keys from the in-memory version map that start with 'fulltext:'."""
        if not self.highest_versions_by_source_id:
            return []
        return [k for k in self.highest_versions_by_source_id.keys() if k.startswith("fulltext:")]
        
    def insert_articles_by_keyword(self, keyword: str, created_by: str, epmc_db: str) -> dict[str, int]:

        json_response = self.epmc_client.get_articles(keyword)
        results = json_response.get("resultList", {}).get("result", []) or []

        affiliations_seen: set[str] = set()

        ingestion_version = self.highest_ingestion_version + 1
        ingestion_model = self.epmc_client.create_ingestion(ingestion_version, created_by=created_by)
        ingestion_id = self.epmc_repo.insert_or_update(ingestion_model, Ingestion, False)
        self.ingestion_id = ingestion_id

        counts = {"records": 0, "articles": 0, "grants": 0, "citations": 0, "references": 0, "fulltexts": 0, "authors": 0, "article_authors": 0, "affiliations": 0}

        try:
            for article in results: 
                
                is_update = self.articles_records.get(article.get("id")) is not None

                # Record
                article_record_model = self.epmc_client.create_record("ARTICLE", keyword)
                article_record_id = self.epmc_repo.insert_or_update(article_record_model, Record, is_update)
                counts["records"] += 1


                citation_data = self.epmc_client.get_citations(article.get("id"))

                # Article
                print(citation_data.get("hitCount"))
                article_entity = self.epmc_client.create_article(article, article_record_id, ingestion_id, created_by=created_by, cited_by=citation_data.get("hitCount", 0))
                article_id = self.epmc_repo.insert_or_update(article_entity, PMCArticle, is_update)
                counts["articles"] += 1
                self.ingested_articles[article.get("id")] = article_id

                for cite in (citation_data.get("citationList") or {}).get("citation") or []:
                    existing_citation = False

                    # Citation
                    citation_entity = self.epmc_client.create_citation(cite, article_id, self.ingestion_id, created_by=created_by)
                    citation_id = self.epmc_repo.insert_or_update(citation_entity, Citation, existing_citation)
                    counts["citations"] += 1

                if article_id not in self.articles_records:
                    self.articles_records[article_id] = article_record_id

                # Grants 
                for grant_data in (article.get("grantsList") or {}).get("grant") or []:                        

                    grant_entity = self.epmc_client.create_grant(grant_data, article_record_id, ingestion_id, created_by=created_by)
                    grant_id = self.epmc_repo.insert_or_update(grant_entity, Grant, is_update)
                    counts["grants"] += 1

                # Fulltext
                for ft in (article.get("fullTextUrlList") or {}).get("fullTextUrl") or []:
                    fulltext_entity = self.epmc_client.create_fulltext(article_id, ft, ingestion_id, created_by=created_by)
                    fulltext_id = self.epmc_repo.insert_or_update(fulltext_entity, FullText, is_update)
                    counts["fulltexts"] += 1
            
                author_order = 1
                for author in (article.get("authorList") or {}).get("author") or []:
                    # Authors
                    existing = self.epmc_repo.get_by_author_name(author.get("fullName"), author.get("firstName"), author.get("lastName"))
                    if existing is None:
                        author_entity = self.epmc_client.create_author(author, ingestion_id, created_by=created_by)
                        author_id = self.epmc_repo.insert_or_update(author_entity, PMCAuthor, is_update)
                        counts["authors"] += 1
                    else:
                        author_id = existing.id
                        counts["authors"] += 1

                    # Article_authors
                    existing_article_author = self.highest_versions_by_source_id.get(
                        f"article_author:{article.get('id')}:{author_id}", 0
                    ) > 0
                           
                    article_author_entity = self.epmc_client.create_article_author(article_id, author_id, author_order, ingestion_id, created_by=created_by)
                    article_author_id = self.epmc_repo.insert_or_update(article_author_entity, ArticleAuthor, existing_article_author)
                    counts["article_authors"] += 1

                    author_order += 1
                
                    # Affiliations
                    aff_order = 1
                    for aff in (author.get("authorAffiliationDetailsList") or {}).get("authorAffiliation", []) or []:
                        org_name = aff.get("affiliation") if isinstance(aff, dict) else aff
                        if org_name and org_name not in affiliations_seen:
                            affiliation_entity = self.epmc_client.create_affiliation(aff, author_id, article_id, aff_order, ingestion_id, created_by=created_by)
                            affiliation_id = self.epmc_repo.insert_or_update(affiliation_entity, PMCAffiliation, is_update)
                            counts["affiliations"] += 1
                            affiliations_seen.add(org_name)
                            aff_order += 1
            
            #ingestion_model = self.epmc_client.update_ingestion(self.ingestion_id, counts["articles"])    
            #self.epmc_repo.update_ingestion_count(ingestion_model, Ingestion) 
            self.epmc_repo.commit_to_db()
        except Exception:
            self.epmc_repo.rollback()
            raise
        print("full article looped")
        return counts
    
    def insert_citations(self, created_by: str):
        
        counts = {"citations": 0}

        if self.ingestion_id is None:
            raise ValueError("Ingestion ID is not set. Please run insert_articles_by_keyword first.")

        for article_id in self.ingested_articles:
            citation_data = self.epmc_client.get_citations(article_id)
            for cite in (citation_data.get("citationList") or {}).get("citation") or []:
                #existing_citation = self.epmc_repo.get_citation(article_id, cite.get("citation_id")) is not None
                existing_citation = False

                # Citation
                citation_entity = self.epmc_client.create_citation(cite, self.ingested_articles[article_id], self.ingestion_id, created_by=created_by)
                citation_id = self.epmc_repo.insert_or_update(citation_entity, Citation, existing_citation)
                counts["citations"] += 1
        return counts

    def insert_references(self, created_by: str, use_db_articles: bool = False):

        counts = {"references": 0}

        # Determine article list: either use self.ingested_articles (from recent ingestion)
        # or fetch all current articles from the database
        if use_db_articles:
            # Fetch all articles from DB; use pm_id as key and internal id for FK
            db_articles = self.epmc_repo.get_all_articles(limit=10000)
            article_map = {str(a.pm_id): a.id for a in db_articles if a.pm_id is not None}
        else:
            # Use articles from recent ingestion (self.ingested_articles key=pm_id, value=internal_id)
            article_map = self.ingested_articles
            if not article_map:
                raise ValueError("Ingestion ID is not set and use_db_articles is False. Please run insert_articles_by_keyword first or set use_db_articles=True.")

        # Create ingestion if needed (for new reference records)
        if self.ingestion_id is None:
            ingestion_version = self.highest_ingestion_version + 1
            ingestion_model = self.epmc_client.create_ingestion(ingestion_version, created_by)
            self.ingestion_id = self.epmc_repo.insert_or_update(ingestion_model, Ingestion, False)

        try:
            for pm_id, article_id in article_map.items():
                response = self.epmc_client.get_references(pm_id)
                reference_items = (response.get("referenceList") or {}).get("reference") or []

                if isinstance(reference_items, dict):
                    reference_items = [reference_items]

                for ref in reference_items:
                    existing_reference = False
                    reference_entity = self.epmc_client.create_reference(ref, article_id, self.ingestion_id, created_by=created_by)
                    reference_id = self.epmc_repo.insert_or_update(reference_entity, Reference, existing_reference)
                    counts["references"] += 1

            self.epmc_repo.commit_to_db()
        except Exception:
            self.epmc_repo.rollback()
            raise

        return counts
    
    def get_unique_authors_count(self) -> int:
        return self.epmc_repo.count_unique_authors()
    
    def get_articles_count(self) -> int:
        return self.epmc_repo.count_articles()
    
    def get_total_citations_count_by_year(self) -> tuple[List[CitationsOverYears], int]:
        return self.epmc_repo.get_total_citations_count_by_year()