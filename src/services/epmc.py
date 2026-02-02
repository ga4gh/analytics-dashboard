from typing import List

from src.clients.epmc import EPMCClient

from src.models.entities.pmc_article import PMCArticle

from src.repositories.epmc import EPMCRepo

from src.models.record import Record, RecordType, Source, Status, ProductType  # Pydantic or DTO, used to build values for RecordEntity if needed


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

            existing = self.epmc_repo.get_by_source_id(article.get("id"))
            is_update = existing is not None  # CHANGE: if existing found, we update

            # Record
            article_record_model = self.create_record("article", keyword)
            article_record_id = self.insert_or_update(self.epmc_repo, article_record_model, is_update)

            # Article
            article_entity = epmc.create_article(article, article_record_id, created_by=created_by)
            article_id = self.insert_or_update(self.epmc_repo, article_entity, is_update)
            counts["articles"] += 1

            # Grants 
            for grant_data in (article.get("grantsList") or {}).get("grant") or []:
                grant_record_model = self.create_record("grant", keyword)
                grant_record_id = self.insert_or_update(self.epmc_repo, grant_record_model, is_update)

 
                grant_entity = epmc.create_grant(grant_data, grant_record_id, created_by=created_by)
                grant_id = self.insert_or_update(self.epmc_repo, grant_entity, is_update)
                counts["grants"] += 1

            # Citations

            citation_data = epmc.get_citations(article.get("id"))
            cite_count = 1
            for cite in (citation_data.get("citationList") or {}).get("citation") or []:
                citation_entity = epmc.create_citation(cite, article_id, cite_count, created_by=created_by)
                citation_id = self.insert_or_update(self.epmc_repo, citation_entity, is_update)
                counts["citations"] += 1
                cite_count += 1

            # References
            response = epmc.get_references(article.get("id"))
            reference_items = (response.get("referenceList") or {}).get("reference") or []

            if isinstance(reference_items, dict):
                reference_items = [reference_items]

            for ref in reference_items:
                reference_entity = epmc.create_reference(ref, article_id, created_by=created_by)
                reference_id = self.insert_or_update(self.epmc_repo, reference_entity, is_update)
                counts["references"] += 1

            # Fulltext
            for ft in (article.get("fullTextUrlList") or {}).get("fullTextUrl") or []:
                fulltext_entity = epmc.create_fulltext(article_id, ft, created_by=created_by)
                fulltext_id = self.insert_or_update(self.epmc_repo, fulltext_entity, is_update)
                counts["fulltexts"] += 1
            
            author_order = 1
            for author in (article.get("authorList") or {}).get("author") or []:
                # Authors
                author_entity = epmc.create_author(author, created_by=created_by)
                author_id = self.insert_or_update(self.epmc_repo, author_entity, is_update)
                counts["authors"] += 1

                # Article_authors
                article_author_entity = epmc.create_article_author(article_id, author_id, author_order, created_by=created_by)
                article_author_id = self.insert_or_update(self.epmc_repo, article_author_entity, is_update)
                counts["article_authors"] += 1

                author_order += 1
                
                # Affiliations
                aff_order = 1
                for aff in (author.get("authorAffiliationDetailsList") or {}).get("authorAffiliation", []) or []:
                    org_name = aff.get("affiliation") if isinstance(aff, dict) else aff
                    if org_name and org_name not in affiliations_seen:
                        affiliation_entity = epmc.create_affiliation(aff, author_id, article_id, aff_order, created_by=created_by)
                        affiliation_id = self.insert_or_update(self.epmc_repo, affiliation_entity, is_update)
                        counts["affiliations"] += 1
                        affiliations_seen.add(org_name)
                        aff_order += 1

        return counts

    def create_grants(self, repo: EPMCRepo, client: EPMCClient, keyword):
        # grants api
        grant_response = client.get_grants(keyword)
        record_list = (grant_response.get("RecordList") or {}).get("Record") or []
        
        if isinstance(record_list, dict):
            record_list = [record_list]

        for gr in record_list:
            is_update = False  # TODO: Implement proper upsert detection (by grant_id, etc.)

            grant_record_model = self.create_record("grant", keyword)
            grant_record_id = self.insert_or_update(self.epmc_repo, grant_record_model, is_update)

            grant_api_entity = client.create_grant_api(gr, grant_record_id)
            self.insert_or_update(repo, grant_api_entity, is_update)

    def create_record(self, type: str, keyword: str) -> Record:
        return Record(
            id="",  
            record_type=RecordType.ARTICLE if type == "article" else RecordType.GRANT,
            source=Source.EUROPE_PMC,
            status=Status.APPROVED,
            keyword=[keyword],
            product_line=ProductType.IMPLEMENTATION,
            created_by="",
            updated_by="",
            version=1,
        )

    def insert_or_update(self, repo: EPMCRepo, entity, update: bool):
        if update:
            entity_id = repo.update(entity)
        else:
            entity_id = repo.insert(entity)
        return entity_id