import os
import uuid
from urllib.parse import urlparse

import pytest
from psycopg import connect, sql

import src.repositories.github as repositories_module
from src.repositories.sqlbuilder import SQLBuilder


RUN_DB_TESTS = os.environ.get("RUN_DB_TESTS") == "1"
DATABASE_URL = os.environ.get("DATABASE_URL")

def _is_true(v):
    return str(v or "").strip().lower() in ("1", "true", "yes", "on")

@pytest.mark.integration
@pytest.mark.skipif(not RUN_DB_TESTS or not DATABASE_URL, reason="Set RUN_DB_TESTS=1 and DATABASE_URL for DB integration tests")
def test_github_repositories_layer_against_postgres():
    # Connect to Postgres
    with connect(DATABASE_URL) as base_conn:
        base_conn.autocommit = True
        cur = base_conn.cursor()
        schema = f"test_repo_layer_{uuid.uuid4().hex[:8]}"
        # Create isolated schema
        cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        # Use schema for subsequent ops
        cur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        cur.close()

        # Use a transactional connection for the test session
        with connect(DATABASE_URL) as conn:
            conn.autocommit = False
            with conn.cursor() as c2:
                c2.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
                conn.commit()

            # Create tables
            with conn.cursor() as c:
                c.execute(
                    sql.SQL("""
                        CREATE TABLE {}.github_repos (
                            id BIGSERIAL PRIMARY KEY,
                            name TEXT NOT NULL,
                            owner TEXT NOT NULL,
                            description TEXT
                        )
                    """).format(sql.Identifier(schema))
                )
                c.execute(
                    sql.SQL("""
                        CREATE TABLE {}.contributor_entity (
                            id BIGSERIAL PRIMARY KEY,
                            name TEXT NOT NULL,
                            type TEXT NOT NULL
                        )
                    """).format(sql.Identifier(schema))
                )
                c.execute(
                    sql.SQL("""
                        CREATE TABLE {}.repo_entity_actions (
                            id BIGSERIAL PRIMARY KEY,
                            repo_id BIGINT NOT NULL,
                            actor TEXT NOT NULL,
                            action TEXT NOT NULL
                        )
                    """).format(sql.Identifier(schema))
                )
                c.execute(
                    sql.SQL("""
                        CREATE TABLE {}.github_archieved_stats (
                            id BIGSERIAL PRIMARY KEY,
                            repo_id BIGINT NOT NULL,
                            weekly_commit_count TEXT
                        )
                    """).format(sql.Identifier(schema))
                )
                conn.commit()

            # Wrap psypg connection so cursor exposes `.cur` with .fetchone(), as expected by insert()
            class CursorWrapper:
                def __init__(self, inner):
                    self._inner = inner
                    self.cur = self  # expose .cur for repo.insert()

                @property
                def description(self):
                    return self._inner.description

                def execute(self, q, params=None):
                    return self._inner.execute(q, params)

                def fetchone(self):
                    return self._inner.fetchone()

                def fetchall(self):
                    return self._inner.fetchall()

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    self._inner.close()

            class ConnectionWrapper:
                def __init__(self, inner):
                    self._inner = inner

                def cursor(self):
                    return CursorWrapper(self._inner.cursor())

                def commit(self):
                    return self._inner.commit()

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    # Don’t close the shared connection here; the outer `with connect(...)` manages it.
                    if exc_type:
                        try:
                            if not self._inner.closed:
                                self._inner.rollback()
                        except Exception:
                            # Avoid masking the original exception
                            pass
                    # Propagate exceptions
                    return False

            class TestDatabaseConnection:
                def __init__(self, inner):
                    self._inner = inner

                def get_connection(self):
                    return ConnectionWrapper(self._inner)

            # Dummy models to avoid pulling real Pydantic classes
            class DummyModel:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)
                    self.id = kwargs.get("id")

                def model_dump(self, exclude=None):
                    data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
                    if exclude:
                        for k in exclude:
                            data.pop(k, None)
                    return data

            # Patch models in the repositories module
            repositories_module.GhRepoModel = DummyModel
            repositories_module.GhEntityModel = DummyModel
            repositories_module.GhEntityActionModel = DummyModel
            repositories_module.GhArchivedStatModel = DummyModel

            # Subclass your SQLBuilder to append RETURNING id for inserts where we need the new id
            class SQLBuilderReturning(SQLBuilder):
                def build_insert(self, data: dict):
                    q, vals = super().build_insert(data)
                    return q + sql.SQL(" RETURNING id"), vals

            # Configure SQL builders with allowed fields
            repo_sqlb = SQLBuilderReturning("github_repos").allow_fields({"id", "name", "owner", "description"})
            entities_sqlb = SQLBuilder("contributor_entity").allow_fields({"id", "name", "type"})
            actions_sqlb = SQLBuilder("repo_entity_actions").allow_fields({"id", "repo_id", "actor", "action"})
            archived_sqlb = SQLBuilder("github_archieved_stats").allow_fields({"id", "repo_id", "weekly_commit_count"})

            # Build repository layer instances
            test_db = TestDatabaseConnection(conn)
            repo_layer = repositories_module.GithubRepo(db=test_db, sql_builder=repo_sqlb)
            entities_layer = repositories_module.GithubEntities(db=test_db, sql_builder=entities_sqlb)
            actions_layer = repositories_module.GithubEntityActions(db=test_db, sql_builder=actions_sqlb)
            archived_layer = repositories_module.GithubArchivedStats(db=test_db, sql_builder=archived_sqlb)

            # ---- GithubRepo insert / get / update / filters ----
            new_id = repo_layer.insert(DummyModel(name="r1", owner="ga4gh", description="first"))
            assert isinstance(new_id, int)

            got = repo_layer.get_by_id(new_id)
            assert got.name == "r1" and got.owner == "ga4gh" and got.description == "first"

            repo_layer.update(new_id, {"description": "updated"})
            got2 = repo_layer.get_by_id(new_id)
            assert got2.description == "updated"

            # Insert another repo
            repo_layer.insert(DummyModel(name="r2", owner="ga4gh", description="second"))
            by_name = repo_layer.get_by_name("r1")
            assert len(by_name) == 1 and by_name[0].id == new_id
            by_owner = repo_layer.get_by_owner("ga4gh")
            assert {r.name for r in by_owner} == {"r1", "r2"}
            all_repos = repo_layer.get_all_repos()
            assert len(all_repos) == 2

            # ---- GithubEntities CRUD ----
            entities_layer.create_entity(DummyModel(name="alice", type="user"))
            entities_layer.create_entity(DummyModel(name="alice", type="org"))
            ents = entities_layer.get_entity_by_name("alice")
            assert len(ents) == 2
            e1 = entities_layer.get_entity_by_id(1)
            assert e1.name == "alice"
            entities_layer.update_entity(DummyModel(id=1, name="alice", type="team"))
            e1b = entities_layer.get_entity_by_id(1)
            assert e1b.type == "team"

            # ---- GithubEntityActions CRUD ----
            actions_layer.create_action(DummyModel(repo_id=1, actor="bob", action="star"))
            actions_layer.create_action(DummyModel(repo_id=1, actor="carol", action="watch"))
            act2 = actions_layer.get_action_by_id(2)
            assert act2.actor == "carol" and act2.action == "watch"
            actions_layer.update_action(DummyModel(id=2, repo_id=1, actor="carol", action="fork"))
            act2b = actions_layer.get_action_by_id(2)
            assert act2b.action == "fork"

            # ---- GithubArchivedStats create/update/get ----
            archived_layer.create_stats(DummyModel(repo_id=10, weekly_commit_count='[1,2,3]'))
            archived_layer.create_stats(DummyModel(repo_id=10, weekly_commit_count='[4,5,6]'))
            stats = archived_layer.get_stats_by_repo_id("10")
            assert len(stats) == 2
            archived_layer.update_stats(DummyModel(id=1, repo_id=10, weekly_commit_count='[7,8,9]'))
            stats_after = archived_layer.get_stats_by_repo_id("10")
            assert any(s.weekly_commit_count == "[7,8,9]" for s in stats_after)

        # Cleanup schema
        with base_conn.cursor() as cleanup:
            cleanup.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))