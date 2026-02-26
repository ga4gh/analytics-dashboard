from typing import List

from src.clients.epmc import EPMCClient

from src.models.entities.pmc_article import PMCArticle
from src.models.entities.pmc_author import PMCAuthor, PMCAffiliation, ArticleAuthor
from src.models.entities.extras import Grant as Grant_Model, FullText, Keyword
from src.models.entities.citations import Citation, Reference
from src.models.entities.record import Record, RecordType, Source, Status, ProductType

from src.repositories.epmc import EPMCRepo



class Grant():
    def __init__(self, repo: EPMCRepo) -> None:
        self.epmc_repo = repo

    def create_grants(self, keyword):
        # grants api
        client = EPMCClient()
        grant_response = client.get_grants(keyword)
        record_list = (grant_response.get("RecordList") or {}).get("Record") or []
        
        if isinstance(record_list, dict):
            record_list = [record_list]

        try:
            for gr in record_list:
                #is_update = self.epmc_repo.get_by_source_id(gr.get("id"), Grant_Model) is not None
                is_update = False

                grant_record_model = client.create_record("GRANT", keyword)
                grant_record_id = self.epmc_repo.insert_or_update(grant_record_model, Record, is_update)

                grant_api_entity = client.create_grant_api(gr, grant_record_id)
                self.epmc_repo.insert_or_update(grant_api_entity, Grant_Model, is_update)

            self.epmc_repo.commit_to_db()
        except Exception:
            self.epmc_repo.rollback()
            raise