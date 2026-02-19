from typing import List
from unittest import skip

from src.clients.epmc import EPMCClient

from src.models.entities.pmc_article import PMCArticle
from src.models.entities.pmc_author import PMCAuthor, PMCAffiliation, ArticleAuthor
from src.models.entities.extras import Grant, FullText, Keyword
from src.models.entities.citations import Citation, Reference
from src.models.entities.record import Record, RecordType, Source, Status, ProductType

from src.repositories.epmc import EPMCRepo

#from src.services.grant import Grant


class EPMCService:
    def __init__(self, repo: EPMCRepo) -> None:
        self.epmc_repo = repo
        
    def get_all_articles(self) -> List[PMCArticle]:
        articles = self.epmc_repo.get_all_articles()
        return articles

    def insert_articles_by_keyword(self, keyword: str, created_by: str, epmc_db: str) -> dict[str, int]:

        epmc = EPMCClient()

        json_response = epmc.get_articles(keyword)
        results = json_response.get("resultList", {}).get("result", []) or []

        affiliations_seen: set[str] = set()

        

        counts = {"records": 0, "articles": 0, "grants": 0, "citations": 0, "references": 0, "fulltexts": 0, "authors": 0, "article_authors": 0, "affiliations": 0}

        for article in results:

            is_update = self.epmc_repo.get_by_source_id(article.get("id")) is not None

            # Record
            article_record_model = epmc.create_record("ARTICLE", keyword)
            article_record_id = self.epmc_repo.insert_or_update(article_record_model, Record, is_update)

            # Article
            article_entity = epmc.create_article(article, article_record_id, created_by=created_by)
            article_id = self.epmc_repo.insert_or_update(article_entity, PMCArticle, is_update)
            counts["articles"] += 1

            # Grants 
            for grant_data in (article.get("grantsList") or {}).get("grant") or []:
                # use article record id for grants associated with article
                existing_grant = self.epmc_repo.get_grant(article_record_id, grant_data.get("grant_id"), grant_data.get("agency"), grant_data.get("doi")) is not None               
                
                grant_entity = epmc.create_grant(grant_data, article_record_id, created_by=created_by)
                grant_id = self.epmc_repo.insert_or_update(grant_entity, Grant, existing_grant)
                counts["grants"] += 1

            # Citations
            citation_data = epmc.get_citations(article.get("id"))
            for cite in (citation_data.get("citationList") or {}).get("citation") or []:
                existing_citation = self.epmc_repo.get_citation(article_id, cite.get("citation_id")) is not None

                citation_entity = epmc.create_citation(cite, article_id, created_by=created_by)
                citation_id = self.epmc_repo.insert_or_update(citation_entity, Citation, existing_citation)
                counts["citations"] += 1

            # References
            response = epmc.get_references(article.get("id"))
            reference_items = (response.get("referenceList") or {}).get("reference") or []

            if isinstance(reference_items, dict):
                reference_items = [reference_items]

            for ref in reference_items:
                existing_reference = self.epmc_repo.get_reference(article_id, ref.get("reference_id")) is not None

                reference_entity = epmc.create_reference(ref, article_id, created_by=created_by)
                reference_id = self.epmc_repo.insert_or_update(reference_entity, Reference, existing_reference)
                counts["references"] += 1

            # Fulltext
            for ft in (article.get("fullTextUrlList") or {}).get("fullTextUrl") or []:
                existing_fulltext = self.epmc_repo.get_fulltext(article_id, ft.get("url")) is not None
                fulltext_entity = epmc.create_fulltext(article_id, ft, created_by=created_by)
                fulltext_id = self.epmc_repo.insert_or_update(fulltext_entity, FullText, existing_fulltext)
                counts["fulltexts"] += 1
            
            author_order = 1
            for author in (article.get("authorList") or {}).get("author") or []:
                # Authors
                existing = self.epmc_repo.get_by_author_name(author.get("fullName"), author.get("firstName"), author.get("lastName"))
                if existing is None:
                    author_entity = epmc.create_author(author, created_by=created_by)
                    author_id = self.epmc_repo.insert_or_update(author_entity, PMCAuthor, is_update)
                    counts["authors"] += 1
                else:
                    author_id = existing.id

                # Article_authors
                existing_article_author = self.epmc_repo.get_articles_authors(article_id, author_id) is not None
                article_author_entity = epmc.create_article_author(article_id, author_id, author_order, created_by=created_by)
                article_author_id = self.epmc_repo.insert_or_update(article_author_entity, ArticleAuthor, existing_article_author)
                counts["article_authors"] += 1

                author_order += 1
                
                # Affiliations
                aff_order = 1
                for aff in (author.get("authorAffiliationDetailsList") or {}).get("authorAffiliation", []) or []:
                    org_name = aff.get("affiliation") if isinstance(aff, dict) else aff
                    if org_name and org_name not in affiliations_seen:
                        existing_affiliation = self.epmc_repo.get_affiliation(article_id, aff.get("reference_id")) is not None
                        affiliation_entity = epmc.create_affiliation(aff, author_id, article_id, aff_order, created_by=created_by)
                        affiliation_id = self.epmc_repo.insert_or_update(affiliation_entity, PMCAffiliation, existing_affiliation)
                        counts["affiliations"] += 1
                        affiliations_seen.add(org_name)
                        aff_order += 1
        print("full article looped")
        return counts


    
