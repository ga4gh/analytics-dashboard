from typing import List, Dict, Any, Optional
from src.models.github import (
    GithubRepo as GhRepoModel,
    GithubEntity as GhEntityModel,
    GithubEntityAction as GhEntityActionModel,
    GithubArchivedStat as GhArchivedStatModel,
)

from .setup import DatabaseConnection


class GithubRepo:
    def __init__(self, db: DatabaseConnection, table_name: str = "github_repos"):
        self.db = db
        self.table_name = table_name

    def create_repo(self, githubRepo: GhRepoModel):
        data = githubRepo.model_dump(exclude={"id"})
        columns = list(data.keys())
        values = tuple(data.values())
        placeholders = ", ".join(["%s"] * len(values))
        query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)                
                conn.commit()

    def update_repo(self, repo_id: int, updates: Dict[str, Any]):
        """
        updates: dict mapping column -> new value (these should match DB column names)
        """
        if not updates:
            return
        set_clauses = ", ".join([f"{col} = %s" for col in updates.keys()])
        values = tuple(updates.values()) + (repo_id,)
        query = f"UPDATE {self.table_name} SET {set_clauses} WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def get_repo_by_id(self, repo_id: int) -> Optional[GhRepoModel]:
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (repo_id,))
                row = cur.fetchone()
                if row:
                    columns = [desc[0] for desc in cur.description]
                    return GhRepoModel(**dict(zip(columns, row)))
                return None

    def get_repo_by_name(self, name: str) -> List[GhRepoModel]:
        query = f"SELECT * FROM {self.table_name} WHERE name = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (name,))
                rows = cur.fetchall()
                if rows:
                    columns = [desc[0] for desc in cur.description]
                    return [GhRepoModel(**dict(zip(columns, row))) for row in rows]
                return []


class GithubEntities:
    def __init__(self, db: DatabaseConnection, table_name: str = "github_entities"):
        self.db = db
        self.table_name = table_name

    def create_entity(self, githubEntity: GhEntityModel):
        data = githubEntity.model_dump(exclude={"id"})
        columns = list(data.keys())
        values = tuple(data.values())
        placeholders = ", ".join(["%s"] * len(values))
        query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def update_entity(self, githubEntity: GhEntityModel):
        data = githubEntity.model_dump(exclude={"id"})
        set_clauses = ", ".join([f"{col} = %s" for col in data.keys()])
        values = tuple(data.values()) + (githubEntity.id,)
        query = f"UPDATE {self.table_name} SET {set_clauses} WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def get_entity_by_id(self, entity_id: int) -> Optional[GhEntityModel]:
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (entity_id,))
                row = cur.fetchone()
                if row:
                    columns = [desc[0] for desc in cur.description]
                    return GhEntityModel(**dict(zip(columns, row)))
                return None

    def get_entity_by_name(self, name: str) -> List[GhEntityModel]:
        query = f"SELECT * FROM {self.table_name} WHERE name = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (name,))
                rows = cur.fetchall()
                if rows:
                    columns = [desc[0] for desc in cur.description]
                    return [GhEntityModel(**dict(zip(columns, row))) for row in rows]
                return []


class GithubEntityActions:
    def __init__(self, db: DatabaseConnection, table_name: str = "github_entity_actions"):
        self.db = db
        self.table_name = table_name

    def create_action(self, githubEntityAction: GhEntityActionModel):
        data = githubEntityAction.model_dump(exclude={"id"})
        columns = list(data.keys())
        values = tuple(data.values())
        placeholders = ", ".join(["%s"] * len(values))
        query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def update_action(self, githubEntityAction: GhEntityActionModel):
        data = githubEntityAction.model_dump(exclude={"id"})
        set_clauses = ", ".join([f"{col} = %s" for col in data.keys()])
        values = tuple(data.values()) + (githubEntityAction.id,)
        query = f"UPDATE {self.table_name} SET {set_clauses} WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def get_action_by_id(self, action_id: int) -> Optional[GhEntityActionModel]:
        query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (action_id,))
                row = cur.fetchone()
                if row:
                    columns = [desc[0] for desc in cur.description]
                    return GhEntityActionModel(**dict(zip(columns, row)))
                return None


class GithubArchivedStats:
    def __init__(self, db: DatabaseConnection, table_name: str = "github_archived_stats"):
        self.db = db
        self.table_name = table_name

    def create_stats(self, githubArchivedStats: GhArchivedStatModel):
        data = githubArchivedStats.model_dump(exclude={"id"})
        columns = list(data.keys())
        values = tuple(data.values())
        placeholders = ", ".join(["%s"] * len(values))
        query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def update_stats(self, githubArchivedStat: GhArchivedStatModel):
        data = githubArchivedStat.model_dump(exclude={"id"})
        set_clauses = ", ".join([f"{col} = %s" for col in data.keys()])
        values = tuple(data.values()) + (githubArchivedStat.id,)
        query = f"UPDATE {self.table_name} SET {set_clauses} WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def get_stats_by_repo_id(self, repo_id: str) -> List[GhArchivedStatModel]:
        query = f"SELECT * FROM {self.table_name} WHERE repo_id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (repo_id,))
                rows = cur.fetchall()
                if rows:
                    columns = [desc[0] for desc in cur.description]
                    return [GhArchivedStatModel(**dict(zip(columns, row))) for row in rows]
                return []
