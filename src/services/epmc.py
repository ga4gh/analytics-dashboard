from typing import List

from src.clients.europePMC import EuropePMC

from src.models.record import Record, RecordType, RecordRequest, Source, Status, ProductType
from src.models.entities.pmc_article import PMCArticle, PMCArticleFull

from src.repositories.epmc import EPMCRepo
from src.repositories.sqlbuilder import SQLBuilder
from src.repositories.record import Record

class EPMCService:
    def __init__(self, repo: EPMCRepo) -> None:
        self.epmc_repo = repo
        
    def get_all_articles(self) -> List[PMCArticleFull]:
        articles = self.epmc_repo.get_all_articles()
        return [PMCArticleFull.model_validate(article) for article in articles]


    def insert_articles_by_keyword(self, keyword: str, created_by: str,
                                   epmc_db: str) -> dict[str, int]:
        epmc = EuropePMC()
        pmc_article_fields = set(PMCArticle.model_fields.keys())
        sql_builder = SQLBuilder.SQLBuilder("pmc_articles").allow_fields(pmc_article_fields - {"id"})
        epmc_repo = EPMCRepo(epmc_db, )
        json_response = epmc.get_articles(keyword)
        results = json_response.get("resultList", {}).get("result", []) or []
        affiliations_list = [] # fetch all affiliations names in db
       
        for article in results:
            
            existing = epmc_repo.get_by_source_id(article.get("id"))
            is_update = existing is None

            # Record
            article_record_model = self.create_record("article", keyword)
            article_record_id = self.insert_or_update(epmc, article_record_model, is_update)

            # Article
            article_model = epmc.create_article(article, article_record_id)
            article_id = self.insert_or_update(epmc, article_model, is_update)

            # Grants
            for grant_data in (article.get("grantsList") or {}).get("grant") or []:

                grant_record_model = self.create_record("article", keyword)
                grant_record_id = self.insert_or_update(epmc, grant_record_model, is_update)


                grant_model = epmc.create_grant(article, grant_data, grant_record_id)
                grant_id = self.insert_or_update(epmc, grant_model, is_update)

            # Citations
            citation_data = epmc.get_citations()
            for cite in (citation_data.get("citationList") or {}).get("citation") or []:
                citations_model = epmc.create_citation(article.get("id"))
                citation_id = self.insert_or_update(epmc, citations_model, is_update)


            # References
            response = epmc.get_references(article.get("id"))
            reference_data = (response.get("referenceList") or {}).get("reference") or []

            if isinstance(reference_data, dict):
                reference_data = [reference_data]

            for ref in reference_data:
                reference_model = epmc.create_reference(article)
                reference_id = self.insert_or_update(epmc, reference_model, is_update)

            # Fulltext
            for ft in (article.get("fullTextUrlList") or {}).get("fullTextUrl") or []:
                fulltext_model = epmc.create_fulltext(article)
                fulltext_id = self.insert_or_update(epmc, fulltext_model, is_update)
            
            author_order = 1
            for author in (article.get("authorList") or {}).get("author") or []:
                
                # Authors
                author_model = epmc.create_author(author)
                author_id = self.insert_or_update(epmc, author_model, is_update)

                # Article_authors
                articles_authors_model =epmc.create_article_author(article, author, author_order, author_id)
                articles_authors_id = self.insert_or_update(epmc, articles_authors_model, is_update)

                author_order +=1
                
                # Affiliations
                for aff in (author.get("authorAffiliationDetailsList") or {}).get("authorAffiliation", []) or []:
                    org_name = aff.get("affiliation") if isinstance(aff, dict) else aff
                    if org_name not in affiliations_list:
                        affiliation_model = epmc.create_affiliation(aff, author_id)
                        affiliation_id = self.insert_or_update(epmc, affiliation_model, is_update)


    def create_grants(self, repo: EPMCRepo, client: EuropePMC, keyword):
        # grants api
        grant_response = repo.get_grants(keyword)
        record_list = (grant_response.get("RecordList") or {}).get("Record") or []
        
        if isinstance(record_list, dict):
            record_list = [record_list]

        for gr in record_list:
            is_update = False #todo
            person = gr.get("Person") or {}
            grant_info = gr.get("Grant") or {}
            institution = gr.get("Institution") or {}
            funder = grant_info.get("Funder") or {}
            amount = grant_info.get("Amount") or {}

            person_aliases = person.get("Alias") or []
            if isinstance(person_aliases, dict):
                person_aliases = [person_aliases]
            
            orcid = ""
            for alias in person_aliases:
                if alias.get("Source") == "ORCID":
                    orcid = alias.get("value")
                    break
            grant_api_model = client.create_grant_api(keyword)
            self.insert_or_update(repo, grant_api_model, is_update)

    def create_record(self, type, keyword):
        return Record(
            id= "",
            record_type= RecordType.ARTICLE if type=="article" else RecordType.GRANT,
            source= Source.EUROPE_PMC,
            status= Status.APPROVED,
            keyword= [keyword],
            product_line= ProductType.IMPLEMENTATION,
            created_by= "",
            updated_by= "",
            version= 1 )

    def insert_or_update(self, repo: EPMCRepo, model, update):
        if update:
            id = repo.update(model)
        else:
            id = repo.insert(model)
        return id
                        
