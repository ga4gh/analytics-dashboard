import pytest
from datetime import datetime
from unittest.mock import Mock
from psycopg import sql

from src.repositories.author import Author as AuthorRepository
from src.repositories.setup import DatabaseConnection
from src.repositories.sqlbuilder import SQLBuilder
from src.models.author import Author as AuthorModel, ArticleType


class TestAuthorRepository:
    
    @pytest.fixture
    def mock_db_connection(self):
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=None)
        
        mock_db = Mock(spec=DatabaseConnection)
        mock_db.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_db.get_connection.return_value.__exit__ = Mock(return_value=None)
        return mock_db, mock_conn, mock_cursor

    @pytest.fixture
    def mock_sql_builder(self):
        return Mock(spec=SQLBuilder)

    @pytest.fixture
    def author_repository(self, mock_db_connection, mock_sql_builder):
        mock_db, _, _ = mock_db_connection
        return AuthorRepository(mock_db, mock_sql_builder)

    @pytest.fixture
    def sample_author(self):
        return AuthorModel(
            id=1,
            article_id=100,
            name="First Last",
            contact="jane.smith@university.edu",
            is_primary=True,
            article_type=ArticleType.ARTICLE,
            created_at=datetime(2025, 1, 1, 10, 0),
            created_by="test_user",
            updated_at=datetime(2025, 1, 1, 10, 0),
            updated_by="test_user",
            version=1
        )

    def test_insert_success(self, author_repository, mock_db_connection, mock_sql_builder, sample_author):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_insert.return_value = (
            sql.SQL("INSERT INTO authors (name, article_id) VALUES (%s, %s)"),
            ("First Last", 100)
        )
        
        author_repository.insert(sample_author)
        
        assert mock_sql_builder.build_insert.call_count == 1
        assert mock_cursor.execute.call_count == 1
        assert mock_conn.commit.call_count == 1
        
        build_insert_call = mock_sql_builder.build_insert.call_args[0][0]
        assert "id" not in build_insert_call
        assert "affiliations" not in build_insert_call

    @pytest.mark.parametrize("sql_builder_error", [
        ValueError("Unknown fields: {'invalid_field'}"),
        ValueError("Database constraint violation"),
        RuntimeError("SQL generation failed"),
    ])
    def test_insert_sql_builder_errors(self, author_repository, mock_db_connection, mock_sql_builder, sample_author, sql_builder_error):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_insert.side_effect = sql_builder_error
        
        with pytest.raises(type(sql_builder_error)) as exc_info:
            author_repository.insert(sample_author)
        
        assert str(exc_info.value) == str(sql_builder_error)
        mock_cursor.execute.assert_not_called()
        mock_conn.commit.assert_not_called()

    @pytest.mark.parametrize("database_error", [
        Exception("Connection failed"),
        RuntimeError("Database constraint violation"),
        ValueError("Invalid data format"),
    ])
    def test_insert_database_errors(self, author_repository, mock_db_connection, mock_sql_builder, sample_author, database_error):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_insert.return_value = (
            sql.SQL("INSERT INTO authors (name) VALUES (%s)"),
            ("First Last",)
        )
        mock_cursor.execute.side_effect = database_error
        
        with pytest.raises(type(database_error)) as exc_info:
            author_repository.insert(sample_author)
        
        assert str(exc_info.value) == str(database_error)
        mock_conn.commit.assert_not_called()

    def test_update_success(self, author_repository, mock_db_connection, mock_sql_builder, sample_author):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_update.return_value = (
            sql.SQL("UPDATE authors SET name = %s WHERE id = %s"),
            ("Updated Name", 1)
        )
        
        author_repository.update(sample_author)
        
        mock_sql_builder.build_update.assert_called_once()
        build_update_args = mock_sql_builder.build_update.call_args
        data, author_id, where_column = build_update_args[0]
        
        assert author_id == sample_author.id
        assert where_column == "id"
        assert "id" not in data
        assert "affiliations" not in data
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @pytest.mark.parametrize("update_error", [
        ValueError("Unknown fields: {'invalid_field'}"),
        RuntimeError("Update failed"),
        Exception("Database connection lost"),
    ])
    def test_update_errors(self, author_repository, mock_db_connection, mock_sql_builder, sample_author, update_error):
        _, mock_conn, mock_cursor = mock_db_connection
        
        if isinstance(update_error, ValueError):
            mock_sql_builder.build_update.side_effect = update_error
        else:
            mock_sql_builder.build_update.return_value = (
                sql.SQL("UPDATE authors SET name = %s WHERE id = %s"),
                ("Name", 1)
            )
            mock_cursor.execute.side_effect = update_error
        
        with pytest.raises(type(update_error)):
            author_repository.update(sample_author)
        
        if not isinstance(update_error, ValueError):
            mock_conn.commit.assert_not_called()

    @pytest.mark.parametrize("author_id,db_row,expected_result", [
        (1, (1, 100, "First Last", "name@email.com", True, "Article", 
             datetime(2025,1,1,10,0), "user1", datetime(2025,1,1,11,0), "user2", None, None, 1), 
         "author_found"),
        (999, None, None),
        (2, (), None),
    ])
    def test_get_by_id(self, author_repository, mock_db_connection, author_id, db_row, expected_result):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.fetchone.return_value = db_row
        if db_row:
            mock_cursor.description = [
                ("id",), ("article_id",), ("name",), ("contact",), ("is_primary",), 
                ("article_type",), ("created_at",), ("created_by",), ("updated_at",), 
                ("updated_by",), ("deleted_at",), ("deleted_by",), ("version",)
            ]
        else:
            mock_cursor.description = None
        
        result = author_repository.get_by_id(author_id)
        
        if expected_result == "author_found":
            assert result is not None
            assert isinstance(result, AuthorModel)
            assert result.id == db_row[0]
            assert result.name == db_row[2]
            assert result.article_id == db_row[1]
        else:
            assert result is None
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM authors WHERE id = %s", (author_id,))

    @pytest.mark.parametrize("article_id,db_rows,expected_count", [
        (100, [
            (1, 100, "First Last", "name@email.com", True, "Article",
             datetime(2025,1,1,10,0), "user1", datetime(2025,1,1,10,0), "user1", None, None, 1),
            (2, 100, "First2 Last2", None, False, "Article",
             datetime(2025,1,1,10,0), "user1", datetime(2025,1,1,10,0), "user1", None, None, 1),
            (3, 100, "First3 Last3", "nsme3@email.com", False, "Grant",
             datetime(2025,1,2,14,0), "user2", datetime(2025,1,2,14,0), "user2", None, None, 1),
        ], 3),
        (999, [], 0),
        (200, [
            (4, 200, "First4 Last4", "name4@email.com", True, "Article",
             datetime(2025,1,3,9,0), "user3", datetime(2025,1,3,9,0), "user3", None, None, 1)
        ], 1),
    ])
    def test_get_by_article_id(self, author_repository, mock_db_connection, article_id, db_rows, expected_count):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.fetchall.return_value = db_rows
        if db_rows:
            mock_cursor.description = [
                ("id",), ("article_id",), ("name",), ("contact",), ("is_primary",), 
                ("article_type",), ("created_at",), ("created_by",), ("updated_at",), 
                ("updated_by",), ("deleted_at",), ("deleted_by",), ("version",)
            ]
        else:
            mock_cursor.description = None
        
        result = author_repository.get_by_article_id(article_id)
        
        assert isinstance(result, list)
        assert len(result) == expected_count
        
        for i, author in enumerate(result):
            assert isinstance(author, AuthorModel)
            assert author.id == db_rows[i][0]
            assert author.article_id == article_id
            assert author.name == db_rows[i][2]
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM authors WHERE article_id = %s", (article_id,))

    @pytest.mark.parametrize("method_name,args", [
        ("get_by_id", (1,)),
        ("get_by_article_id", (100,)),
    ])
    def test_database_connection_errors(self, author_repository, mock_db_connection, method_name, args):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.execute.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception) as exc_info:
            getattr(author_repository, method_name)(*args)
        
        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.parametrize("method_name,mock_description,return_value", [
        ("get_by_id", None, (1, 100, "Name")),
        ("get_by_article_id", None, [(1, 100, "Name")]),
    ])
    def test_missing_cursor_description(self, author_repository, mock_db_connection, method_name, mock_description, return_value):
        _, _, mock_cursor = mock_db_connection
        
        if method_name == "get_by_id":
            mock_cursor.fetchone.return_value = return_value
            mock_cursor.description = mock_description
            result = author_repository.get_by_id(1)
            assert result is None
        else:
            mock_cursor.fetchall.return_value = return_value
            mock_cursor.description = mock_description
            result = author_repository.get_by_article_id(100)
            assert result == []

    @pytest.mark.parametrize("method_name,empty_return", [
        ("get_by_id", None),
        ("get_by_article_id", []),
    ])
    def test_empty_cursor_description(self, author_repository, mock_db_connection, method_name, empty_return):
        _, _, mock_cursor = mock_db_connection
        
        if method_name == "get_by_id":
            mock_cursor.fetchone.return_value = (1, 100, "Name")
            mock_cursor.description = []
            result = author_repository.get_by_id(1)
            assert result is None
        else:
            mock_cursor.fetchall.return_value = [(1, 100, "Name")]
            mock_cursor.description = []
            result = author_repository.get_by_article_id(100)
            assert result == []