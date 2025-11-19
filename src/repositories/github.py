from typing import List, Dict, Any, Optional
from src.models.github import (
    GithubRepo as GhRepoModel,
    GithubEntity as GhEntityModel,
    GithubEntityAction as GhEntityActionModel,
    GithubArchivedStat as GhArchivedStatModel,
)

from .setup import DatabaseConnection
from .sqlbuilder import SQLBuilder


class GithubRepo:
    def __init__(self, db: DatabaseConnection, sql_builder: SQLBuilder) -> None:
        self.db = db
        self.sql_builder = sql_builder

    def insert(self, githubRepo: GhRepoModel) -> None:
        data = githubRepo.model_dump(exclude={"id"})
        query, values = self.sql_builder.build_insert(data)

        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, values)
            repo_id = cur.cur.fetchone()[0]
            conn.commit()
            return repo_id

    def update(self, githubRepo_id: int, updates: Dict[str, Any]) -> None:
        if not updates:
            return
        query, values = self.sql_builder.build_update(updates, githubRepo_id, "id")

        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, values)
            conn.commit()

    def get_by_id(self, repo_id: int) -> Optional[GhRepoModel]:
        query = f"SELECT * FROM github_repos WHERE id = %s"
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (repo_id,))
            row = cur.fetchone()
            if row and cur.description:
                columns = [desc[0] for desc in cur.description]
                data = dict(zip(columns, row, strict=False))
                return GhRepoModel(**data)
            return None

    def get_by_name(self, name: str) -> List[GhRepoModel]:
        query = f"SELECT * FROM github_repos WHERE name = %s"
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (name,))
            rows = cur.fetchall()
            if rows and cur.description:
                columns = [desc[0] for desc in cur.description]
                repos: List[GhRepoModel] = []
                for row in rows:
                    data = dict(zip(columns, row, strict=False))
                    repos.append(GhRepoModel(**data))
                return repos
            return []
    
    def get_by_owner(self, owner: str) -> List[GhRepoModel]:
        query = f"SELECT * FROM github_repos WHERE owner = %s"
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (owner,))
            rows = cur.fetchall()
            if rows and cur.description:
                columns = [desc[0] for desc in cur.description]
                repos: List[GhRepoModel] = []
                for row in rows:
                    data = dict(zip(columns, row, strict=False))
                    repos.append(GhRepoModel(**data))
                return repos
            return []
    
    def get_all_repos(self) -> List[GhRepoModel]:
        query = f"SELECT * FROM github_repos"
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            if rows and cur.description:
                columns = [desc[0] for desc in cur.description]
                repos: List[GhRepoModel] = []
                for row in rows:
                    data = dict(zip(columns, row, strict=False))
                    repos.append(GhRepoModel(**data))
                return repos
            return []

class GithubArchivedStats:
    def __init__(self, db: DatabaseConnection, sql_builder: SQLBuilder):
        self.db = db
        self.sql_builder = sql_builder

    def create_stats(self, githubArchivedStats: GhArchivedStatModel) -> None:
        data = githubArchivedStats.model_dump(exclude={"id"})
        query, values = self.sql_builder.build_insert(data)

        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, values)
            conn.commit()

    def update_stats(self, githubArchivedStat: GhArchivedStatModel) -> None:
        data = githubArchivedStat.model_dump(exclude={"id"})
        query, values = self.sql_builder.build_update(data, githubArchivedStat.id, "id")

        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, values)
            conn.commit()

    def get_stats_by_repo_id(self, repo_id: str) -> List[GhArchivedStatModel]:
        query = f"SELECT * FROM github_archieved_stats WHERE repo_id = %s"
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (repo_id,))
            rows = cur.fetchall()
            if rows and cur.description:
                columns = [desc[0] for desc in cur.description]
                stats: List[GhArchivedStatModel] = []
                for row in rows:
                    data = dict(zip(columns, row, strict=False))
                    stats.append(GhArchivedStatModel(**data))
                return stats
            return []


class GithubEntities:
    def __init__(self, db: DatabaseConnection, sql_builder: SQLBuilder) -> None:
        self.db = db
        self.sql_builder = sql_builder

    def create_entity(self, githubEntity: GhEntityModel) -> None:
        data = githubEntity.model_dump(exclude={"id"})
        query, values = self.sql_builder.build_insert(data)

        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, values)
            conn.commit()

    def update_entity(self, githubEntity: GhEntityModel) -> None:
        data = githubEntity.model_dump(exclude={"id"})
        query, values = self.sql_builder.build_update(data, githubEntity.id, "id")

        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, values)
            conn.commit()

    def get_entity_by_id(self, entity_id: int) -> Optional[GhEntityModel]:
        query = f"SELECT * FROM contributor_entity WHERE id = %s"
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (entity_id,))
            row = cur.fetchone()
            if row and cur.description:
                columns = [desc[0] for desc in cur.description]
                data = dict(zip(columns, row, strict=False))
                return GhEntityModel(**data)
            return None

    def get_entity_by_name(self, name: str) -> List[GhEntityModel]:
        query = f"SELECT * FROM contributor_entity WHERE name = %s"
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (name,))
            rows = cur.fetchall()
            if rows and cur.description:
                columns = [desc[0] for desc in cur.description]
                entities: List[GhEntityModel] = []
                for row in rows:
                    data = dict(zip(columns, row, strict=False))
                    entities.append(GhEntityModel(**data))
                return entities
            return []


class GithubEntityActions:
    def __init__(self, db: DatabaseConnection, sql_builder: SQLBuilder) -> None:
        self.db = db
        self.sql_builder = sql_builder

    def create_action(self, githubEntityAction: GhEntityActionModel) -> None:
        data = githubEntityAction.model_dump(exclude={"id"})
        query, values = self.sql_builder.build_insert(data)

        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, values)
            conn.commit()

    def update_action(self, githubEntityAction: GhEntityActionModel) -> None:
        data = githubEntityAction.model_dump(exclude={"id"})
        query, values = self.sql_builder.build_update(data, githubEntityAction.id, "id")

        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, values)
            conn.commit()

    def get_action_by_id(self, action_id: int) -> Optional[GhEntityActionModel]:
        query = f"SELECT * FROM repo_entity_actions WHERE id = %s"
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (action_id,))
            row = cur.fetchone()
            if row and cur.description:
                columns = [desc[0] for desc in cur.description]
                data = dict(zip(columns, row, strict=False))
                return GhEntityActionModel(**data)
            return None



