import pytest

import src.repositories.github as repositories_module


# ----------------------------
# Test doubles and helpers
# ----------------------------
class FakeCursor:
    def __init__(self, description=None, fetchone_row=None, fetchall_rows=None, returning_insert_id=None):
        # DB-API-like attributes
        self.description = description
        self._fetchone_row = fetchone_row
        self._fetchall_rows = fetchall_rows or []
        self.executed = []
        self.closed = False
        # For GithubRepo.insert, the code does: cur.cur.fetchone()[0]
        # Provide a "cur" object that has a .fetchone() method returning the insert id tuple.
        if returning_insert_id is not None:
            self.cur = type("InnerCur", (), {"fetchone": staticmethod(lambda: (returning_insert_id,))})()
        else:
            # Fallback to a no-op inner cursor
            self.cur = type("InnerCur", (), {"fetchone": staticmethod(lambda: None)})()

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self._fetchone_row

    def fetchall(self):
        return list(self._fetchall_rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor: FakeCursor):
        self._cursor = cursor
        self.commits = 0
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.closed = True


class FakeDB:
    def __init__(self, cursor: FakeCursor = None):
        self._cursor = cursor or FakeCursor()
        self.connections_opened = 0
        self.last_connection = None

    def get_connection(self):
        self.connections_opened += 1
        conn = FakeConnection(self._cursor)
        self.last_connection = conn
        return conn


class FakeSQLBuilder:
    def __init__(self, insert_response=None, update_response=None):
        # You can override responses per test
        self.insert_response = insert_response or ("INSERT INTO t (...) VALUES (...)", ("v1", "v2"))
        self.update_response = update_response or ("UPDATE t SET ... WHERE id = %s", ("v1", "v2"))
        self.last_insert_data = None
        self.last_update_args = None

    def build_insert(self, data):
        self.last_insert_data = dict(data)
        return self.insert_response

    def build_update(self, updates, pk_value, pk_field):
        self.last_update_args = {"updates": dict(updates), "pk_value": pk_value, "pk_field": pk_field}
        return self.update_response


class DummyModel:
    """Simple replacement for Pydantic models used in the repositories layer."""
    def __init__(self, **kwargs):
        self._data = dict(kwargs)
        # Expose id if present
        self.id = kwargs.get("id")

    def model_dump(self, exclude=None):
        data = dict(self._data)
        if exclude:
            for k in exclude:
                data.pop(k, None)
        return data

    @property
    def data(self):
        return dict(self._data)


# ----------------------------
# Auto-patch repository module models to DummyModel
# ----------------------------
@pytest.fixture(autouse=True)
def patch_models(monkeypatch):
    monkeypatch.setattr(repositories_module, "GhRepoModel", DummyModel, raising=True)
    monkeypatch.setattr(repositories_module, "GhEntityModel", DummyModel, raising=True)
    monkeypatch.setattr(repositories_module, "GhEntityActionModel", DummyModel, raising=True)
    monkeypatch.setattr(repositories_module, "GhArchivedStatModel", DummyModel, raising=True)


# ----------------------------
# GithubRepo unit tests
# ----------------------------
def test_github_repo_insert_returns_new_id_and_commits():
    # Arrange: builder returns some SQL; cursor is prepared to return a generated id via cur.cur.fetchone()[0]
    builder = FakeSQLBuilder()
    cursor = FakeCursor(returning_insert_id=42)
    db = FakeDB(cursor)

    repo_layer = repositories_module.GithubRepo(db=db, sql_builder=builder)

    model = DummyModel(id=999, name="repo1", owner="org", description="test")
    # Act
    new_id = repo_layer.insert(model)

    # Assert builder received data without id
    assert builder.last_insert_data == {"name": "repo1", "owner": "org", "description": "test"}
    # Ensure execute was called with builder's SQL and values
    assert cursor.executed == [builder.insert_response]
    # Returned id propagated from cursor.cur.fetchone()
    assert new_id == 42
    # Commit happened
    assert db.last_connection.commits == 1


def test_github_repo_update_noop_on_empty_updates():
    builder = FakeSQLBuilder()
    db = FakeDB(FakeCursor())
    repo_layer = repositories_module.GithubRepo(db=db, sql_builder=builder)

    repo_layer.update(githubRepo_id=10, updates={})

    assert builder.last_update_args is None
    # No connection opened
    assert db.connections_opened == 0


def test_github_repo_update_executes_and_commits():
    builder = FakeSQLBuilder()
    cursor = FakeCursor()
    db = FakeDB(cursor)
    repo_layer = repositories_module.GithubRepo(db=db, sql_builder=builder)

    updates = {"description": "updated", "owner": "ga4gh"}
    repo_layer.update(githubRepo_id=5, updates=updates)

    assert builder.last_update_args == {"updates": updates, "pk_value": 5, "pk_field": "id"}
    assert cursor.executed == [builder.update_response]
    assert db.last_connection.commits == 1


def test_github_repo_get_by_id_found():
    columns = [("id",), ("name",), ("owner",), ("description",)]
    row = (7, "r1", "ga4gh", "desc")
    cursor = FakeCursor(description=columns, fetchone_row=row)
    db = FakeDB(cursor)
    repo_layer = repositories_module.GithubRepo(db=db, sql_builder=FakeSQLBuilder())

    res = repo_layer.get_by_id(7)

    assert isinstance(res, DummyModel)
    assert res.data == {"id": 7, "name": "r1", "owner": "ga4gh", "description": "desc"}
    # Ensure query and params recorded
    q, p = cursor.executed[0]
    assert "FROM github_repos WHERE id = %s" in q
    assert p == (7,)


def test_github_repo_get_by_id_not_found():
    cursor = FakeCursor(description=[("id",)], fetchone_row=None)
    db = FakeDB(cursor)
    repo_layer = repositories_module.GithubRepo(db=db, sql_builder=FakeSQLBuilder())

    assert repo_layer.get_by_id(999) is None


def test_github_repo_get_by_name_returns_list():
    columns = [("id",), ("name",), ("owner",)]
    rows = [(1, "repo", "ga4gh"), (2, "repo", "other")]
    cursor = FakeCursor(description=columns, fetchall_rows=rows)
    db = FakeDB(cursor)
    repo_layer = repositories_module.GithubRepo(db=db, sql_builder=FakeSQLBuilder())

    res = repo_layer.get_by_name("repo")
    assert [r.data for r in res] == [
        {"id": 1, "name": "repo", "owner": "ga4gh"},
        {"id": 2, "name": "repo", "owner": "other"},
    ]
    q, p = cursor.executed[0]
    assert "FROM github_repos WHERE name = %s" in q
    assert p == ("repo",)


def test_github_repo_get_by_owner_returns_list():
    columns = [("id",), ("name",), ("owner",)]
    rows = [(1, "r1", "ga4gh"), (2, "r2", "ga4gh")]
    cursor = FakeCursor(description=columns, fetchall_rows=rows)
    db = FakeDB(cursor)
    repo_layer = repositories_module.GithubRepo(db=db, sql_builder=FakeSQLBuilder())

    res = repo_layer.get_by_owner("ga4gh")
    assert [r.data for r in res] == [
        {"id": 1, "name": "r1", "owner": "ga4gh"},
        {"id": 2, "name": "r2", "owner": "ga4gh"},
    ]
    q, p = cursor.executed[0]
    assert "FROM github_repos WHERE owner = %s" in q
    assert p == ("ga4gh",)


def test_github_repo_get_all_repos_returns_list():
    columns = [("id",), ("name",), ("owner",)]
    rows = [(1, "r1", "ga4gh"), (2, "r2", "ga4gh")]
    cursor = FakeCursor(description=columns, fetchall_rows=rows)
    db = FakeDB(cursor)
    repo_layer = repositories_module.GithubRepo(db=db, sql_builder=FakeSQLBuilder())

    res = repo_layer.get_all_repos()
    assert [r.data for r in res] == [
        {"id": 1, "name": "r1", "owner": "ga4gh"},
        {"id": 2, "name": "r2", "owner": "ga4gh"},
    ]
    q, p = cursor.executed[0]
    assert q.strip() == "SELECT * FROM github_repos"
    assert p is None


# ----------------------------
# GithubArchivedStats unit tests
# ----------------------------
def test_archived_stats_create_and_update_commits():
    builder = FakeSQLBuilder()
    cursor = FakeCursor()
    db = FakeDB(cursor)
    layer = repositories_module.GithubArchivedStats(db=db, sql_builder=builder)

    create_model = DummyModel(id=1, repo_id=10, weekly_commit_count=[1, 2, 3])
    layer.create_stats(create_model)
    assert builder.last_insert_data == {"repo_id": 10, "weekly_commit_count": [1, 2, 3]}
    assert cursor.executed[-1] == builder.insert_response
    assert db.last_connection.commits == 1

    update_model = DummyModel(id=1, repo_id=10, weekly_commit_count=[4, 5, 6])
    layer.update_stats(update_model)
    assert builder.last_update_args == {
        "updates": {"repo_id": 10, "weekly_commit_count": [4, 5, 6]},
        "pk_value": 1,
        "pk_field": "id",
    }
    assert cursor.executed[-1] == builder.update_response
    assert db.last_connection.commits == 1


def test_archived_stats_get_by_repo_id_returns_list():
    columns = [("id",), ("repo_id",), ("weekly_commit_count",)]
    rows = [(1, 10, [1, 2, 3]), (2, 10, [4, 5, 6])]
    cursor = FakeCursor(description=columns, fetchall_rows=rows)
    db = FakeDB(cursor)
    layer = repositories_module.GithubArchivedStats(db=db, sql_builder=FakeSQLBuilder())

    stats = layer.get_stats_by_repo_id("10")
    assert [s.data for s in stats] == [
        {"id": 1, "repo_id": 10, "weekly_commit_count": [1, 2, 3]},
        {"id": 2, "repo_id": 10, "weekly_commit_count": [4, 5, 6]},
    ]
    q, p = cursor.executed[0]
    assert "FROM github_archieved_stats WHERE repo_id = %s" in q
    assert p == ("10",)


# ----------------------------
# GithubEntities unit tests
# ----------------------------
def test_entities_create_update_and_getters():
    builder = FakeSQLBuilder()
    cursor = FakeCursor()
    db = FakeDB(cursor)
    layer = repositories_module.GithubEntities(db=db, sql_builder=builder)

    # create
    create_model = DummyModel(id=5, name="alice", type="user")
    layer.create_entity(create_model)
    assert builder.last_insert_data == {"name": "alice", "type": "user"}
    assert cursor.executed[-1] == builder.insert_response
    assert db.last_connection.commits == 1

    # update
    update_model = DummyModel(id=5, name="alice", type="org")
    layer.update_entity(update_model)
    assert builder.last_update_args == {"updates": {"name": "alice", "type": "org"}, "pk_value": 5, "pk_field": "id"}
    assert cursor.executed[-1] == builder.update_response
    assert db.last_connection.commits == 1

    # get by id
    columns = [("id",), ("name",), ("type",)]
    row = (5, "alice", "org")
    cursor2 = FakeCursor(description=columns, fetchone_row=row)
    db2 = FakeDB(cursor2)
    layer2 = repositories_module.GithubEntities(db=db2, sql_builder=FakeSQLBuilder())
    ent = layer2.get_entity_by_id(5)
    assert isinstance(ent, DummyModel)
    assert ent.data == {"id": 5, "name": "alice", "type": "org"}

    # get by name
    rows = [(6, "alice", "user"), (7, "alice", "org")]
    cursor3 = FakeCursor(description=columns, fetchall_rows=rows)
    db3 = FakeDB(cursor3)
    layer3 = repositories_module.GithubEntities(db=db3, sql_builder=FakeSQLBuilder())
    ents = layer3.get_entity_by_name("alice")
    assert [e.data for e in ents] == [
        {"id": 6, "name": "alice", "type": "user"},
        {"id": 7, "name": "alice", "type": "org"},
    ]


# ----------------------------
# GithubEntityActions unit tests
# ----------------------------
def test_entity_actions_create_update_and_get_by_id():
    builder = FakeSQLBuilder()
    cursor = FakeCursor()
    db = FakeDB(cursor)
    layer = repositories_module.GithubEntityActions(db=db, sql_builder=builder)

    # create
    create_model = DummyModel(id=9, repo_id=1, actor="bob", action="star")
    layer.create_action(create_model)
    assert builder.last_insert_data == {"repo_id": 1, "actor": "bob", "action": "star"}
    assert cursor.executed[-1] == builder.insert_response
    assert db.last_connection.commits == 1

    # update
    update_model = DummyModel(id=9, repo_id=1, actor="bob", action="watch")
    layer.update_action(update_model)
    assert builder.last_update_args == {
        "updates": {"repo_id": 1, "actor": "bob", "action": "watch"},
        "pk_value": 9,
        "pk_field": "id",
    }
    assert cursor.executed[-1] == builder.update_response
    assert db.last_connection.commits == 1

    # get by id
    columns = [("id",), ("repo_id",), ("actor",), ("action",)]
    row = (9, 1, "bob", "watch")
    cursor2 = FakeCursor(description=columns, fetchone_row=row)
    db2 = FakeDB(cursor2)
    layer2 = repositories_module.GithubEntityActions(db=db2, sql_builder=FakeSQLBuilder())
    act = layer2.get_action_by_id(9)
    assert isinstance(act, DummyModel)
    assert act.data == {"id": 9, "repo_id": 1, "actor": "bob", "action": "watch"}