from typing import List

from src.clients.epmc import EPMCClient

from src.models.entities.ingestion import Ingestion
from src.models.entities.pmc_article import PMCArticle
from src.models.entities.pmc_author import PMCAuthor, PMCAffiliation, ArticleAuthor
from src.models.entities.extras import Grant as Grant_Model, FullText, Keyword
from src.models.entities.citations import Citation, Reference
from src.models.entities.record import Record, RecordType, Source, Status, ProductType

from src.repositories.epmc import EPMCRepo



class GrantService:
    def __init__(self, repo: EPMCRepo) -> None:
        self.epmc_repo = repo
        self.epmc_client = EPMCClient()
        self.grants_records: dict[str, int] = self._load_grants_records()
        self.highest_versions_by_source_id: dict[str, int] = self._load_versions_by_source_id()
        self.highest_ingestion_version = repo.get_highest_ingestion_version()
        self.ingestion_id = None

    def _load_grants_records(self) -> dict[str, int]:
        """Return a mapping of grant source identifier -> record_id.

        Uses the `grants` table's `grant_id` column and `record_id` FK.
        """
        result: dict[str, int] = {}
        try:
            for g in self.epmc_repo.get_all_grants():
                if getattr(g, "grant_id", None) is not None:
                    result[str(g.grant_id)] = int(g.record_id)
        except Exception:
            # If repository access fails, return empty mapping.
            return {}
        return result

    def _load_versions_by_source_id(self) -> dict[str, int]:
        """Delegate to repo.get_max_version_by_source_id() to obtain current versions."""
        try:
            return self.epmc_repo.get_max_version_by_source_id()
        except Exception:
            return {}

    def create_grants(self, keyword):
        # grants api

        counts = {"grants": 0}
        grant_response = self.epmc_client.get_grants(keyword)
        record_list = (grant_response.get("RecordList") or {}).get("Record") or []

        ingestion_version = self.highest_ingestion_version + 1
        ingestion_model = self.epmc_client.create_ingestion(ingestion_version, "system")
        ingestion_id = self.epmc_repo.insert_or_update(ingestion_model, Ingestion, False)
        self.ingestion_id = ingestion_id

        if isinstance(record_list, dict):
            record_list = [record_list]

        try:
            for gr in record_list:
                #is_update = self.epmc_repo.get_by_source_id(gr.get("id"), Grant_Model) is not None
                is_update = False

                grant_record_model = self.epmc_client.create_record("GRANT", keyword)
                grant_record_id = self.epmc_repo.insert_or_update(grant_record_model, Record, is_update)

                grant_api_entity = self.epmc_client.create_grant_api(gr, grant_record_id, ingestion_id)
                self.epmc_repo.insert_or_update(grant_api_entity, Grant_Model, is_update)
                counts["grants"] += 1

            self.epmc_repo.commit_to_db()
        except Exception:
            self.epmc_repo.rollback()
            raise
        return counts