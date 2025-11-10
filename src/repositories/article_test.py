import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from psycopg import sql

from src.repositories.article import Article as ArticleRepository
from src.repositories.setup import DatabaseConnection
from src.repositories.sqlbuilder import SQLBuilder
from src.models.article import Article as ArticleModel, Status


class TestArticleRepository:
    
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
    def article_repository(self, mock_db_connection, mock_sql_builder):
        mock_db, _, _ = mock_db_connection
        return ArticleRepository(mock_db, mock_sql_builder)

    @pytest.fixture
    def sample_article(self):
        return ArticleModel(
            id=1,
            record_id=100,
            title="Test Article",
            abstract="Test abstract content",
            journal="Test Journal",
            source_id="test_source_123",
            doi="10.1234/test",
            status=Status.PUBLISHED,
            publish_date=datetime(2025, 1, 1),
            link="https://test.example.com/article",
            created_at=datetime(2025, 1, 1, 10, 0),
            created_by="test_user",
            updated_at=datetime(2025, 1, 1, 10, 0),
            updated_by="test_user",
            version=1
        )

    @pytest.mark.parametrize("article_id", [
        (123),
        (456),
        (999),
        (1),
    ])
    def test_insert_success(self, article_repository, mock_db_connection, mock_sql_builder, sample_article, article_id):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_insert.return_value = (
            sql.SQL("INSERT INTO articles (title, journal) VALUES (%s, %s) RETURNING id"),
            ("Test Article", "Test Journal")
        )
        mock_cursor.fetchone.return_value = [article_id]
        
        result = article_repository.insert(sample_article)
        
        assert result == article_id
        assert mock_sql_builder.build_insert.call_count == 1
        assert mock_cursor.execute.call_count == 1
        assert mock_cursor.fetchone.call_count == 1
        assert mock_conn.commit.call_count == 1
        
        build_insert_call = mock_sql_builder.build_insert.call_args[0][0]
        assert "id" not in build_insert_call
        assert "authors" not in build_insert_call

    @pytest.mark.parametrize("sql_builder_error", [
        ValueError("Unknown fields: {'invalid_field'}"),
        ValueError("Database constraint violation"),
        RuntimeError("SQL generation failed"),
    ])
    def test_insert_sql_builder_errors(self, article_repository, mock_db_connection, mock_sql_builder, sample_article, sql_builder_error):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_insert.side_effect = sql_builder_error
        
        with pytest.raises(type(sql_builder_error)) as exc_info:
            article_repository.insert(sample_article)
        
        assert str(exc_info.value) == str(sql_builder_error)
        mock_cursor.execute.assert_not_called()
        mock_conn.commit.assert_not_called()

    @pytest.mark.parametrize("database_error", [
        Exception("Connection failed"),
        RuntimeError("Database constraint violation"),
        ValueError("Invalid data format"),
    ])
    def test_insert_database_errors(self, article_repository, mock_db_connection, mock_sql_builder, sample_article, database_error):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_insert.return_value = (
            sql.SQL("INSERT INTO articles (title) VALUES (%s) RETURNING id"),
            ("Test Article",)
        )
        mock_cursor.execute.side_effect = database_error
        
        with pytest.raises(type(database_error)) as exc_info:
            article_repository.insert(sample_article)
        
        assert str(exc_info.value) == str(database_error)
        mock_conn.commit.assert_not_called()

    def test_update_success(self, article_repository, mock_db_connection, mock_sql_builder, sample_article):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_update.return_value = (
            sql.SQL("UPDATE articles SET title = %s WHERE id = %s"),
            ("Updated Title", 1)
        )
        
        article_repository.update(sample_article)
        
        mock_sql_builder.build_update.assert_called_once()
        build_update_args = mock_sql_builder.build_update.call_args
        data, article_id, where_column = build_update_args[0]
        
        assert article_id == sample_article.id
        assert where_column == "id"
        assert "id" not in data
        assert "authors" not in data
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @pytest.mark.parametrize("update_error", [
        ValueError("Unknown fields: {'invalid_field'}"),
        RuntimeError("Update failed"),
        Exception("Database connection lost"),
    ])
    def test_update_errors(self, article_repository, mock_db_connection, mock_sql_builder, sample_article, update_error):
        _, mock_conn, mock_cursor = mock_db_connection
        
        if isinstance(update_error, ValueError):
            mock_sql_builder.build_update.side_effect = update_error
        else:
            mock_sql_builder.build_update.return_value = (
                sql.SQL("UPDATE articles SET title = %s WHERE id = %s"),
                ("Title", 1)
            )
            mock_cursor.execute.side_effect = update_error
        
        with pytest.raises(type(update_error)):
            article_repository.update(sample_article)
        
        if not isinstance(update_error, ValueError):
            mock_conn.commit.assert_not_called()

    @pytest.mark.parametrize("article_id,db_row,expected_result", [
        (1, (1, 100, "Title", "Abstract", "Journal", "src_123", "10.1234/test", 
             "Published", datetime(2025,1,1), "https://link.com", 
             datetime(2025,1,1,10,0), "user", datetime(2025,1,1,11,0), "user2", None, None, 1), 
         "article_found"),
        (999, None, None),
        (2, (), None),
    ])
    def test_get_by_id(self, article_repository, mock_db_connection, article_id, db_row, expected_result):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.fetchone.return_value = db_row
        if db_row:
            mock_cursor.description = [
                ("id",), ("record_id",), ("title",), ("abstract",), ("journal",), 
                ("source_id",), ("doi",), ("status",), ("publish_date",), ("link",),
                ("created_at",), ("created_by",), ("updated_at",), ("updated_by",), 
                ("deleted_at",), ("deleted_by",), ("version",)
            ]
        else:
            mock_cursor.description = None
        
        result = article_repository.get_by_id(article_id)
        
        if expected_result == "article_found":
            assert result is not None
            assert isinstance(result, ArticleModel)
            assert result.id == db_row[0]
            assert result.title == db_row[2]
            assert result.journal == db_row[4]
        else:
            assert result is None
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM articles WHERE id = %s", (article_id,))

    @pytest.mark.parametrize("source_id,db_row,expected_result", [
        ("test_123", (1, 100, "Title", None, "Journal", "test_123", None, 
         "Unknown", None, None, datetime(2025,1,1), "user", 
         datetime(2025,1,1), "user", None, None, 1), "article_found"),
        ("nonexistent", None, None),
        ("empty_result", (), None),
    ])
    def test_get_by_source_id(self, article_repository, mock_db_connection, source_id, db_row, expected_result):
        mock_db, mock_conn, mock_cursor = mock_db_connection
        
        mock_cursor.fetchone.return_value = db_row
        if db_row:
            mock_cursor.description = [
                ("id",), ("record_id",), ("title",), ("abstract",), ("journal",), 
                ("source_id",), ("doi",), ("status",), ("publish_date",), ("link",),
                ("created_at",), ("created_by",), ("updated_at",), ("updated_by",), 
                ("deleted_at",), ("deleted_by",), ("version",)
            ]
        else:
            mock_cursor.description = None
        
        result = article_repository.get_by_source_id(source_id)
        
        if expected_result == "article_found":
            assert result is not None
            assert isinstance(result, ArticleModel)
            assert result.source_id == source_id
        else:
            assert result is None
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM articles WHERE source_id = %s", (source_id,))

    @pytest.mark.parametrize("keyword,db_rows,expected_count", [
        ("ga4gh", [
            (1, 100, "Title1", "Abstract1", "Journal1", "src_1", "doi_1", 
             "Published", datetime(2025,1,1), "link1", datetime(2025,1,1), "user", 
             datetime(2025,1,1), "user", None, None, 1),
            (2, 101, "Title2", "Abstract2", "Journal2", "src_2", "doi_2", 
             "Published", datetime(2025,1,2), "link2", datetime(2025,1,2), "user", 
             datetime(2025,1,2), "user", None, None, 1),
        ], 2),
        ("ga3gh", [], 0),
        ("DRS", [
            (3, 102, "Title", "Abstract", "Journal", "src_3", "doi_3", 
             "Preprint", None, "link3", datetime(2025,1,3), "user", 
             datetime(2025,1,3), "user", None, None, 1)
        ], 1),
    ])
    def test_get_by_keyword(self, article_repository, mock_db_connection, keyword, db_rows, expected_count):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.fetchall.return_value = db_rows
        if db_rows:
            mock_cursor.description = [
                ("id",), ("record_id",), ("title",), ("abstract",), ("journal",), 
                ("source_id",), ("doi",), ("status",), ("publish_date",), ("link",),
                ("created_at",), ("created_by",), ("updated_at",), ("updated_by",), 
                ("deleted_at",), ("deleted_by",), ("version",)
            ]
        else:
            mock_cursor.description = None
        
        result = article_repository.get_by_keyword(keyword)
        
        assert isinstance(result, list)
        assert len(result) == expected_count
        
        for i, article in enumerate(result):
            assert isinstance(article, ArticleModel)
            assert article.id == db_rows[i][0]
            assert article.title == db_rows[i][2]
        
        expected_query = """
            SELECT a.* FROM articles a
            JOIN records r ON a.record_id = r.id
            WHERE %s = ANY(r.keyword)
        """
        mock_cursor.execute.assert_called_once_with(expected_query, (keyword,))

    @pytest.mark.parametrize("keyword,start_date,end_date,db_rows,expected_count", [
        ("ga4gh", datetime(2025,1,1), datetime(2025,12,31), [
            (1, 100, "Title1", "Abstract1", "Journal1", "src_1", "doi_1", 
             "Published", datetime(2025,6,1), "link1", datetime(2025,1,1), "user", 
             datetime(2025,1,1), "user", None, None, 1)
        ], 1),
        ("ga4gh", datetime(2025,1,1), datetime(2025,6,30), [], 0),
        ("ga4gh", datetime(2020,1,1), datetime(2025,1,1), [
            (2, 101, "Title2", "Abstract2", "Journal2", "src_2", "doi_2", 
             "Published", datetime(2024,1,2), "link2", datetime(2025,1,2), "user", 
             datetime(2025,1,2), "user", None, None, 1),
            (3, 102, "Title", "Abstract", "Journal", "src_3", "doi_3", 
             "Published", datetime(2020,2,2), "link3", datetime(2025,1,3), "user", 
             datetime(2025,1,3), "user", None, None, 1)
        ], 2),
    ])
    def test_get_by_keyword_and_date(self, article_repository, mock_db_connection, keyword, start_date, end_date, db_rows, expected_count):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.fetchall.return_value = db_rows
        if db_rows:
            mock_cursor.description = [
                ("id",), ("record_id",), ("title",), ("abstract",), ("journal",), 
                ("source_id",), ("doi",), ("status",), ("publish_date",), ("link",),
                ("created_at",), ("created_by",), ("updated_at",), ("updated_by",), 
                ("deleted_at",), ("deleted_by",), ("version",)
            ]
        else:
            mock_cursor.description = None
        
        result = article_repository.get_by_keyword_and_date(keyword, start_date, end_date)
        
        assert isinstance(result, list)
        assert len(result) == expected_count
        
        for i, article in enumerate(result):
            assert isinstance(article, ArticleModel)
            assert article.id == db_rows[i][0]
            if article.publish_date:
                assert start_date <= article.publish_date <= end_date
        
        expected_query = """
            SELECT a.* FROM articles a
            JOIN records r ON a.record_id = r.id
            WHERE %s = ANY(r.keyword) AND a.publish_date BETWEEN %s AND %s
        """
        mock_cursor.execute.assert_called_once_with(expected_query, (keyword, start_date, end_date))

    @pytest.mark.parametrize("keyword,status,db_rows,expected_count", [
        ("ga4gh", "Published", [
            (1, 100, "Title1", "Abstract1", "Journal1", "src_1", "doi_1", 
             "Published", datetime(2025,6,1), "link1", datetime(2025,1,1), "user", 
             datetime(2025,1,1), "user", None, None, 1)
        ], 1),
        ("ga4gh", "Preprint", [
            (2, 101, "Preprint 1", "Abstract", "Journal", "pre_1", "doi_2", 
             "Preprint", datetime(2025,2,1), "link2", datetime(2025,2,1), "user", 
             datetime(2025,2,1), "user", None, None, 1),
            (3, 102, "Preprint 2", "Abstract", "Journal", "pre_2", "doi_3", 
             "Preprint", datetime(2025,3,1), "link3", datetime(2025,3,1), "user", 
             datetime(2025,3,1), "user", None, None, 1)
        ], 2),
        ("ga3gh", "Unknown", [], 0)
    ])
    def test_get_by_keyword_and_status(self, article_repository, mock_db_connection, keyword, status, db_rows, expected_count):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.fetchall.return_value = db_rows
        if db_rows:
            mock_cursor.description = [
                ("id",), ("record_id",), ("title",), ("abstract",), ("journal",), 
                ("source_id",), ("doi",), ("status",), ("publish_date",), ("link",),
                ("created_at",), ("created_by",), ("updated_at",), ("updated_by",), 
                ("deleted_at",), ("deleted_by",), ("version",)
            ]
        else:
            mock_cursor.description = None
        
        result = article_repository.get_by_keyword_and_status(keyword, status)
        
        assert isinstance(result, list)
        assert len(result) == expected_count
        
        for i, article in enumerate(result):
            assert isinstance(article, ArticleModel)
            assert article.id == db_rows[i][0]
            assert article.status == status
        
        expected_query = """
            SELECT a.* FROM articles a
            JOIN records r ON a.record_id = r.id
            WHERE %s = ANY(r.keyword) AND a.status = %s
        """
        mock_cursor.execute.assert_called_once_with(expected_query, (keyword, status))

    @pytest.mark.parametrize("method_name,args", [
        ("get_by_id", (1,)),
        ("get_by_source_id", ("test_source",)),
        ("get_by_keyword", ("test_keyword",)),
        ("get_by_keyword_and_date", ("keyword", datetime(2025,1,1), datetime(2025,12,31))),
        ("get_by_keyword_and_status", ("keyword", "Published")),
    ])
    def test_database_connection_errors(self, article_repository, mock_db_connection, method_name, args):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.execute.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception) as exc_info:
            getattr(article_repository, method_name)(*args)
        
        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.parametrize("method_name,mock_description", [
        ("get_by_id", None),
        ("get_by_source_id", None),
        ("get_by_keyword", []),
        ("get_by_keyword_and_date", []),
        ("get_by_keyword_and_status", []),
    ])
    def test_missing_cursor_description(self, article_repository, mock_db_connection, method_name, mock_description):
        _, _, mock_cursor = mock_db_connection
        
        if "get_by_id" in method_name or "get_by_source_id" in method_name:
            mock_cursor.fetchone.return_value = (1, 100, "Title")
            mock_cursor.description = mock_description
            result = getattr(article_repository, method_name)(1 if "id" in method_name else "test")
            assert result is None
        else:
            mock_cursor.fetchall.return_value = [(1, 100, "Title")]
            mock_cursor.description = mock_description
            args = ("keyword", datetime(2025,1,1), datetime(2025,12,31)) if "date" in method_name else \
                   ("keyword", "Published") if "status" in method_name else ("keyword",)
            result = getattr(article_repository, method_name)(*args)
            assert result == []