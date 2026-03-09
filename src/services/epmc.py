from typing import List
from unittest import skip

from src.clients.epmc import EPMCClient

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
        self.articles_records: dict[str, int] = self._load_articles_records()
        self.highest_versions_by_source_id: dict[str, int] = self._load_versions_by_source_id()

    def _load_articles_records(self) -> dict[str, int]:
        article_rows = self.epmc_repo.get_all_articles_ids()
        return {
            pm_id: record_id
            for pm_id, record_id in article_rows
            if pm_id is not None
        }
    
    def _load_versions_by_source_id(self) -> dict[str, int]:
        return self.epmc_repo.get_max_version_by_source_id()

    def _normalize_url(self, url: str | None) -> str:
        """Normalize URLs for stable lookups: strip whitespace, lowercase, and remove trailing slash."""
        if not url:
            return ""
        s = str(url).strip()
        s = s.lower()
        # remove trailing slash for consistency
        if s.endswith("/"):
            s = s.rstrip("/")
        return s

    def list_fulltext_keys(self) -> list[str]:
        """Return all keys from the in-memory version map that start with 'fulltext:'."""
        if not self.highest_versions_by_source_id:
            return []
        return [k for k in self.highest_versions_by_source_id.keys() if k.startswith("fulltext:")]
        
    def insert_articles_by_keyword(self, keyword: str, created_by: str, epmc_db: str) -> dict[str, int]:

        json_response = self.epmc_client.get_articles(keyword)
        results = json_response.get("resultList", {}).get("result", []) or []

        affiliations_seen: set[str] = set()

        counts = {"records": 0, "articles": 0, "grants": 0, "citations": 0, "references": 0, "fulltexts": 0, "authors": 0, "article_authors": 0, "affiliations": 0}

        try:
            for article in results: 

                is_update = self.articles_records.get(article.get("id")) is not None

                # Record
                #ingestion_model = self.epmc_client.create_ingestion(created_by=created_by)
                #record_ingestion_id = self.epmc_repo.insert_or_update(ingestion_model, Ingestion, False)

                article_record_model = self.epmc_client.create_record("ARTICLE", keyword)
                article_record_id = self.epmc_repo.insert_or_update(article_record_model, Record, is_update)
                counts["records"] += 1


                # Article
                article_version = self.highest_versions_by_source_id.get(f"article:{article.get('id')}", 0) + 1
                article_ingestion_model = self.epmc_client.create_ingestion(article_version, created_by=created_by)
                article_ingestion_id = self.epmc_repo.insert_or_update(article_ingestion_model, Ingestion, False)

                article_entity = self.epmc_client.create_article(article, article_record_id, article_ingestion_id, created_by=created_by)
                article_id = self.epmc_repo.insert_or_update(article_entity, PMCArticle, is_update)
                counts["articles"] += 1

                if article_id not in self.articles_records:
                    self.articles_records[article_id] = article_record_id

                # Grants 
                for grant_data in (article.get("grantsList") or {}).get("grant") or []:
                   
                    existing_grant = self.epmc_repo.get_grant(article_record_id, grant_data.get("grant_id"), grant_data.get("agency"), grant_data.get("doi")) is not None               

                    # Grand version but going to use article version for consistency
                    #grant_source_id = grant_data.get("grantId") or grant_data.get("grant_id")
                    #grant_version = self.highest_versions_by_source_id.get(f"grant:{grant_source_id}", 0) + 1
                    #grant_version = article_version if article_version > grant_version else grant_version
                    grant_version = article_version
                    grant_ingestion_model = self.epmc_client.create_ingestion(grant_version, created_by=created_by)
                    grant_ingestion_id = self.epmc_repo.insert_or_update(grant_ingestion_model, Ingestion, False)

                    grant_entity = self.epmc_client.create_grant(grant_data, article_record_id, grant_ingestion_id, created_by=created_by)
                    grant_id = self.epmc_repo.insert_or_update(grant_entity, Grant, existing_grant)
                    counts["grants"] += 1

                # Fulltext
                for ft in (article.get("fullTextUrlList") or {}).get("fullTextUrl") or []:
                    # version logic 
                    raw_url = ft.get("url")
                    norm_url = self._normalize_url(raw_url)
                    existing_fulltext = self.highest_versions_by_source_id.get(f"fulltext:{norm_url}", 0) > 0
                    #fulltext_version = self.highest_versions_by_source_id.get(f"fulltext:{norm_url}", 0) + 1
                    fulltext_version = article_version

                    fulltext_ingestion_model = self.epmc_client.create_ingestion(fulltext_version, created_by=created_by)
                    fulltext_ingestion_id = self.epmc_repo.insert_or_update(fulltext_ingestion_model, Ingestion, False)

                    fulltext_entity = self.epmc_client.create_fulltext(article_id, ft, fulltext_ingestion_id, created_by=created_by)
                    fulltext_id = self.epmc_repo.insert_or_update(fulltext_entity, FullText, existing_fulltext)
                    counts["fulltexts"] += 1
            
                author_order = 1
                for author in (article.get("authorList") or {}).get("author") or []:
                    # Authors
                    existing = self.epmc_repo.get_by_author_name(author.get("fullName"), author.get("firstName"), author.get("lastName"))
                    if existing is None:
                        #author_version = self.highest_versions_by_source_id.get(f"author:{author.get('fullName')}", 0) + 1
                        author_version = article_version
                        
                        author_ingestion_model = self.epmc_client.create_ingestion(author_version, created_by=created_by)
                        author_ingestion_id = self.epmc_repo.insert_or_update(author_ingestion_model, Ingestion, False)

                        author_entity = self.epmc_client.create_author(author, author_ingestion_id, created_by=created_by)
                        author_id = self.epmc_repo.insert_or_update(author_entity, PMCAuthor, is_update)
                        counts["authors"] += 1
                    else:
                        author_id = existing.id
                        counts["authors"] += 1

                    # Article_authors
                    existing_article_author = self.highest_versions_by_source_id.get(f"article_author:{article.get("id")}:{author_id}", 0) > 0

                    if self.highest_versions_by_source_id.get(f"article_author:{article.get("id")}:{author_id}", 0) == 0:
                        return 0
                    
                    #article_author_version = self.highest_versions_by_source_id.get(f"article_author:{article.get("id")}:{author_id}", 0) + 1
                    article_author_version = article_version
                    
                    article_author_ingestion_model = self.epmc_client.create_ingestion(article_author_version, created_by=created_by)
                    article_author_ingestion_id = self.epmc_repo.insert_or_update(article_author_ingestion_model, Ingestion, False)

                    article_author_entity = self.epmc_client.create_article_author(article_id, author_id, author_order, article_author_ingestion_id, created_by=created_by)
                    article_author_id = self.epmc_repo.insert_or_update(article_author_entity, ArticleAuthor, existing_article_author)
                    counts["article_authors"] += 1

                    author_order += 1
                
                    # Affiliations
                    aff_order = 1
                    for aff in (author.get("authorAffiliationDetailsList") or {}).get("authorAffiliation", []) or []:
                        org_name = aff.get("affiliation") if isinstance(aff, dict) else aff
                        if org_name and org_name not in affiliations_seen:
                            existing_affiliation = self.highest_versions_by_source_id.get(f"affiliation:{article.get('id')}:{author_id}", 0) > 0

                            #affiliation_version = self.highest_versions_by_source_id.get(f"affiliation:{article.get('id')}:{author_id}", 0) + 1
                            affiliation_version = article_version
                            affiliation_ingestion_model = self.epmc_client.create_ingestion(affiliation_version, created_by=created_by)
                            affiliation_ingestion_id = self.epmc_repo.insert_or_update(affiliation_ingestion_model, Ingestion, False)

                            affiliation_entity = self.epmc_client.create_affiliation(aff, author_id, article_id, aff_order, affiliation_ingestion_id, created_by=created_by)
                            affiliation_id = self.epmc_repo.insert_or_update(affiliation_entity, PMCAffiliation, existing_affiliation)
                            counts["affiliations"] += 1
                            affiliations_seen.add(org_name)
                            aff_order += 1

            self.epmc_repo.commit_to_db()
        except Exception:
            self.epmc_repo.rollback()
            raise
        print("full article looped")
        return counts
    
    def get_all_citations(self, created_by: str):
        for article_id in self.articles_records.keys():
            citation_data = self.epmc_client.get_citations(article_id)
            for cite in (citation_data.get("citationList") or {}).get("citation") or []:
                existing_citation = self.epmc_repo.get_citation(article_id, cite.get("citation_id")) is not None

                # Citation
                citation_version = self.highest_versions_by_source_id.get(f"citation:{cite.get('id')}", 0) + 1
                citation_ingestion_model = self.epmc_client.create_ingestion(citation_version, created_by=created_by)
                citation_ingestion_id = self.epmc_repo.insert_or_update(citation_ingestion_model, Ingestion, False)

                citation_entity = self.epmc_client.create_citation(cite, article_id, citation_ingestion_id, created_by=created_by)
                citation_id = self.epmc_repo.insert_or_update(citation_entity, Citation, existing_citation)

    def get_all_references(self, created_by: str):
        for article_id in self.articles_records.keys():
            response = self.epmc_client.get_references(article_id)
            reference_items = (response.get("referenceList") or {}).get("reference") or []

            if isinstance(reference_items, dict):
                reference_items = [reference_items]

            for ref in reference_items:
                existing_reference = self.epmc_repo.get_reference(article_id, ref.get("reference_id")) is not None

                # Reference
                reference_version = self.highest_versions_by_source_id.get(f"reference:{ref.get('id')}", 0) + 1
                reference_ingestion_model = self.epmc_client.create_ingestion(reference_version, created_by=created_by)
                reference_ingestion_id = self.epmc_repo.insert_or_update(reference_ingestion_model, Ingestion, False)

                reference_entity = self.epmc_client.create_reference(ref, article_id, reference_ingestion_id, created_by=created_by)
                reference_id = self.epmc_repo.insert_or_update(reference_entity, Reference, existing_reference)



    
