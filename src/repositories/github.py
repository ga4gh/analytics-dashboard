from src.models.github import GithubRepo, GithubEntity, GithubEntityAction, GithubArchievedStat
from .setup import DatabaseConnection

class GithubRepo:
    def __init__(self, db: DatabaseConnection, table_name: str):
        self.db = db
        self.table_name = table_name

    def create_github_repo(self, githubRepo: GithubRepo):
        data = githubRepo.model_dump(exclude={'id'})
        columns = list(data.keys())
        values = tuple(data.values())
        placeholders = ', '.join(['%s'] * len(values))

        query = f"INSERT INTO github_repos ({', '.join(columns)}) VALUES ({placeholders})"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def update_github_repo(self, githubRepo: GithubRepo):
        data = githubRepo.model_dump(exclude={'id'})
        set_clauses = ', '.join([f"{col} = %s" for col in data.keys()])
        values = tuple(data.values()) + (githubRepo.id,)

        query = f"UPDATE github_repos SET {set_clauses} WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                print("executing")
                cur.execute(query, values)
                conn.commit()

    def get_github_repo_by_id(self, repo_id: int):
        query = "SELECT * FROM github_repos WHERE id = %s"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (repo_id,))
                row = cur.fetchone()

                if row:
                    columns = [desc[0] for desc in cur.description]
                    data = dict(zip(columns, row))
                    return GithubRepo(**data)
                return None

    def get_github_repo_by_name(self, name: str):
        query = "SELECT * FROM github_repos WHERE name = %s"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (name,))
                rows = cur.fetchall()

                if rows:
                    columns = [desc[0] for desc in cur.description]
                    repos = []
                    for row in rows:
                        data = dict(zip(columns, row))
                        repos.append(GithubRepo(**data))
                    return repos
                return []



class GithubEntity:
    def __init__(self, db: DatabaseConnection, table_name: str):
        self.db = db
        self.table_name = table_name

    def create_github_entity(self, githubEntity: GithubEntity):
        data = githubEntity.model_dump(exclude={'id'})
        columns = list(data.keys())
        values = tuple(data.values())
        placeholders = ', '.join(['%s'] * len(values))

        query = f"INSERT INTO github_entity ({', '.join(columns)}) VALUES ({placeholders})"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def update_github_entity(self, githubEntity: GithubEntity):
        data = githubEntity.model_dump(exclude={'id'})
        set_clauses = ', '.join([f"{col} = %s" for col in data.keys()])
        values = tuple(data.values()) + (githubEntity.id,)

        query = f"UPDATE github_entity SET {set_clauses} WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                print("executing")
                cur.execute(query, values)
                conn.commit()

    def get_github_entity_by_id(self, repo_id: int):
        query = "SELECT * FROM github_entity WHERE id = %s"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (repo_id,))
                row = cur.fetchone()

                if row:
                    columns = [desc[0] for desc in cur.description]
                    data = dict(zip(columns, row))
                    return GithubEntity(**data)
                return None

    def get_github_entity_by_name(self, name: str):
        query = "SELECT * FROM github_entity WHERE name = %s"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (name,))
                rows = cur.fetchall()

                if rows:
                    columns = [desc[0] for desc in cur.description]
                    entity = []
                    for row in rows:
                        data = dict(zip(columns, row))
                        entity.append(GithubEntity(**data))
                    return entity
                return []

class GithubEntityActions:
    def __init__(self, db: DatabaseConnection, table_name: str):
        self.db = db
        self.table_name = table_name

    def create_github_entity_actions(self, githubEntityActions: GithubEntityAction):
        data = githubEntityActions.model_dump(exclude={'id'})
        columns = list(data.keys())
        values = tuple(data.values())
        placeholders = ', '.join(['%s'] * len(values))

        query = f"INSERT INTO github_entity_actions ({', '.join(columns)}) VALUES ({placeholders})"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def update_github_entity_actions(self, githubEntityActions: GithubEntityAction):
        data = githubEntityActions.model_dump(exclude={'id'})
        set_clauses = ', '.join([f"{col} = %s" for col in data.keys()])
        values = tuple(data.values()) + (githubEntityActions.id,)

        query = f"UPDATE github_entity_actions SET {set_clauses} WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                print("executing")
                cur.execute(query, values)
                conn.commit()

    def get_github_entity_actions_by_id(self, repo_id: int):
        query = "SELECT * FROM github_entity_actions WHERE id = %s"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (repo_id,))
                row = cur.fetchone()

                if row:
                    columns = [desc[0] for desc in cur.description]
                    data = dict(zip(columns, row))
                    return GithubEntityAction(**data)
                return None

    def get_github_entity_actions_by_name(self, name: str):
        query = "SELECT * FROM github_entity_actions WHERE name = %s"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (name,))
                rows = cur.fetchall()

                if rows:
                    columns = [desc[0] for desc in cur.description]
                    actions = []
                    for row in rows:
                        data = dict(zip(columns, row))
                        actions.append(GithubEntityAction(**data))
                    return actions
                return []

class GithubArchievedStats:
    def __init__(self, db: DatabaseConnection, table_name: str):
        self.db = db
        self.table_name = table_name

    def create_github_archieved_stats(self, githubArchievedStats: GithubArchievedStat):
        data = githubArchievedStats.model_dump(exclude={'id'})
        columns = list(data.keys())
        values = tuple(data.values())
        placeholders = ', '.join(['%s'] * len(values))

        query = f"INSERT INTO github_archieved_stats ({', '.join(columns)}) VALUES ({placeholders})"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def update_github_archieved_stats(self, githubArchievedStat: GithubArchievedStat):
        data = githubArchievedStat.model_dump(exclude={'id'})
        set_clauses = ', '.join([f"{col} = %s" for col in data.keys()])
        values = tuple(data.values()) + (githubArchievedStat.id,)

        query = f"UPDATE github_archieved_stats SET {set_clauses} WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                print("executing")
                cur.execute(query, values)
                conn.commit()

    def get_github_archieved_stats_by_id(self, repo_id: int):
        query = "SELECT * FROM github_archieved_stats WHERE id = %s"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (repo_id,))
                row = cur.fetchone()

                if row:
                    columns = [desc[0] for desc in cur.description]
                    data = dict(zip(columns, row))
                    return GithubArchievedStat(**data)
                return None

    def get_github_archieved_stats_by_name(self, name: str):
        query = "SELECT * FROM github_archieved_stats WHERE name = %s"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (name,))
                rows = cur.fetchall()

                if rows:
                    columns = [desc[0] for desc in cur.description]
                    stats = []
                    for row in rows:
                        data = dict(zip(columns, row))
                        stats.append(GithubArchievedStat(**data))
                    return stats
                return []