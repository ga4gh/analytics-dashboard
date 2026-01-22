from typing import List
from src.models.pmc_article import PMCArticle, PMCArticleFull
from src.repositories.epmc import EPMCRepo as EPMCRepo
from src.clients.europePMC import EuropePMC
from src.repositories.record import Record
from src.models.record import Record, RecordType, RecordRequest, Source, Status, ProductType
from src.repositories.epmc import EPMCRepo
from src.repositories.sqlbuilder import SQLBuilder

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

        update = True #temp
        #grant = epmc.create_grant_api(keyword)
        
        id = 10000
        for article in results:
            
            # Record
            record_model = Record(
                    id= "",
                    record_type= RecordType.ARTICLE,
                    source= Source.EUROPE_PMC,
                    status= Status.APPROVED,
                    keyword= [keyword],
                    product_line= ProductType.IMPLEMENTATION,
                    created_by= "",
                    updated_by= "",
                    version= 1 )
            if update:
                record_id = epmc_repo.update(record_model)
            else:
                record_id = epmc_repo.insert(record_model)


            # Article
            article_model = epmc.create_article(article, id)
            if update:
                article_id = epmc_repo.update(article_model)
            else:
                article_id = epmc_repo.insert(article_model)


            # Grants
            for grant_data in (article.get("grantsList") or {}).get("grant") or []:
                grant_model = epmc.create_grant(article, grant_data)
                if update:
                    grant_id = epmc_repo.update(grant_model)
                else:
                    grant_id = epmc_repo.insert(grant_model)

            # Citations
            citation_data = epmc.get_citations()
            for cite in (citation_data.get("citationList") or {}).get("citation") or []:
                citations_model = epmc.create_citation(article.get("id"))
                if update:
                    citation_id = epmc_repo.update(citations_model)
                else:
                    citation_id = epmc_repo.insert(citations_model)

            # References
            response = epmc.get_references(article.get("id"))
            reference_data = (response.get("referenceList") or {}).get("reference") or []

            if isinstance(reference_data, dict):
                reference_data = [reference_data]

            for ref in reference_data:
                reference_model = epmc.create_reference(article)
                if update:
                    reference_id = epmc_repo.update(reference_model)
                else:
                    reference_id = epmc_repo.insert(reference_model)

            # Fulltext
            for ft in (article.get("fullTextUrlList") or {}).get("fullTextUrl") or []:
                fulltext_model = epmc.create_fulltext(article)
                if update:
                    fulltext_id = epmc_repo.update(fulltext_model)
                else:
                    fulltext_id = epmc_repo.insert(fulltext_model)

            # Authors
            id += 1
            author_order = 1
            for author in (article.get("authorList") or {}).get("author") or []:
                
                author_model = epmc.create_author(author)
                if update:
                    author_id = epmc_repo.update(author_model)
                else:
                    author_id = epmc_repo.insert(author_model)

                articles_authors_model =epmc.create_article_author(article, author, author_order)
                if update:
                    articles_authors_id = epmc_repo.update(articles_authors_model)
                else:
                    articles_authors_id = epmc_repo.insert(articles_authors_model)
                author_order +=1
                
                # Affiliations
                for aff in (author.get("authorAffiliationDetailsList") or {}).get("authorAffiliation", []) or []:
                    org_name = aff.get("affiliation") if isinstance(aff, dict) else aff
                    if org_name not in affiliations_list:
                        affiliation_model = epmc.create_affiliation(aff)
                        if update:
                            affiliation_id = epmc_repo.update(affiliation_model)
                        else:
                            affiliation_id = epmc_repo.insert(affiliation_model)
                        
