import pytest
from datetime import datetime
from unittest.mock import Mock
from psycopg import sql

from src.repositories.record import Record as RecordRepository
from src.repositories.setup import DatabaseConnection
from src.repositories.sqlbuilder import SQLBuilder
from src.models.record import Record as RecordModel, RecordType, Source, Status, ProductType


class TestRecordRepository:
    
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
    def record_repository(self, mock_db_connection, mock_sql_builder):
        mock_db, _, _ = mock_db_connection
        return RecordRepository(mock_db, mock_sql_builder)

    @pytest.fixture
    def sample_record(self):
        return RecordModel(
            id=1,
            record_type=RecordType.ARTICLE,
            source=Source.PUBMED,
            status=Status.APPROVED,
            keyword=["genomics", "bioinformatics", "ga4gh"],
            product_line=ProductType.STANDARD,
            created_at=datetime(2025, 1, 1, 10, 0),
            created_by="test_user",
            updated_at=datetime(2025, 1, 1, 10, 0),
            updated_by="test_user",
            version=1
        )

    @pytest.mark.parametrize("record_id", [
        123,
        456,
        999,
        1,
    ])
    def test_insert_success(self, record_repository, mock_db_connection, mock_sql_builder, sample_record, record_id):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_insert.return_value = (
            sql.SQL("INSERT INTO records (record_type, source) VALUES (%s, %s) RETURNING id"),
            ("Article", "PubMed")
        )
        mock_cursor.fetchone.return_value = [record_id]
        
        result = record_repository.insert(sample_record)
        
        assert result == record_id
        assert mock_sql_builder.build_insert.call_count == 1
        assert mock_cursor.execute.call_count == 1
        assert mock_cursor.fetchone.call_count == 1
        assert mock_conn.commit.call_count == 1
        
        build_insert_call = mock_sql_builder.build_insert.call_args[0][0]
        assert "id" not in build_insert_call

    @pytest.mark.parametrize("sql_builder_error", [
        ValueError("Unknown fields: {'invalid_field'}"),
        ValueError("Database constraint violation"),
        RuntimeError("SQL generation failed"),
    ])
    def test_insert_sql_builder_errors(self, record_repository, mock_db_connection, mock_sql_builder, sample_record, sql_builder_error):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_insert.side_effect = sql_builder_error
        
        with pytest.raises(type(sql_builder_error)) as exc_info:
            record_repository.insert(sample_record)
        
        assert str(exc_info.value) == str(sql_builder_error)
        mock_cursor.execute.assert_not_called()
        mock_conn.commit.assert_not_called()

    @pytest.mark.parametrize("database_error", [
        Exception("Connection failed"),
        RuntimeError("Database constraint violation"),
        ValueError("Invalid data format"),
    ])
    def test_insert_database_errors(self, record_repository, mock_db_connection, mock_sql_builder, sample_record, database_error):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_insert.return_value = (
            sql.SQL("INSERT INTO records (record_type) VALUES (%s) RETURNING id"),
            ("Article",)
        )
        mock_cursor.execute.side_effect = database_error
        
        with pytest.raises(type(database_error)) as exc_info:
            record_repository.insert(sample_record)
        
        assert str(exc_info.value) == str(database_error)
        mock_conn.commit.assert_not_called()

    def test_update_success(self, record_repository, mock_db_connection, mock_sql_builder, sample_record):
        _, mock_conn, mock_cursor = mock_db_connection
        
        mock_sql_builder.build_update.return_value = (
            sql.SQL("UPDATE records SET status = %s WHERE id = %s"),
            ("Rejected", 1)
        )
        
        record_repository.update(sample_record)
        
        mock_sql_builder.build_update.assert_called_once()
        build_update_args = mock_sql_builder.build_update.call_args
        data, record_id, where_column = build_update_args[0]
        
        assert record_id == sample_record.id
        assert where_column == "id"
        assert "id" not in data
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @pytest.mark.parametrize("update_error", [
        ValueError("Unknown fields: {'invalid_field'}"),
        RuntimeError("Update failed"),
        Exception("Database connection lost"),
    ])
    def test_update_errors(self, record_repository, mock_db_connection, mock_sql_builder, sample_record, update_error):
        _, mock_conn, mock_cursor = mock_db_connection
        
        if isinstance(update_error, ValueError):
            mock_sql_builder.build_update.side_effect = update_error
        else:
            mock_sql_builder.build_update.return_value = (
                sql.SQL("UPDATE records SET status = %s WHERE id = %s"),
                ("Approved", 1)
            )
            mock_cursor.execute.side_effect = update_error
        
        with pytest.raises(type(update_error)):
            record_repository.update(sample_record)
        
        if not isinstance(update_error, ValueError):
            mock_conn.commit.assert_not_called()

    @pytest.mark.parametrize("record_id,db_row,expected_result", [
        (1, (1, "Article", "PubMed", "Approved", ["ga4gh", "beacon"], "standard",
             datetime(2025,1,1,10,0), "user1", datetime(2025,1,1,11,0), "user2", None, None, 1), 
         "record_found"),
        (999, None, None),
        (2, (), None),
    ])
    def test_get_by_id(self, record_repository, mock_db_connection, record_id, db_row, expected_result):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.fetchone.return_value = db_row
        if db_row:
            mock_cursor.description = [
                ("id",), ("record_type",), ("source",), ("status",), ("keyword",), 
                ("product_line",), ("created_at",), ("created_by",), ("updated_at",), 
                ("updated_by",), ("deleted_at",), ("deleted_by",), ("version",)
            ]
        else:
            mock_cursor.description = None
        
        result = record_repository.get_by_id(record_id)
        
        if expected_result == "record_found":
            assert result is not None
            assert isinstance(result, RecordModel)
            assert result.id == db_row[0]
            assert result.record_type == db_row[1]
            assert result.source == db_row[2]
            assert result.status == db_row[3]
        else:
            assert result is None
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM records WHERE id = %s", (record_id,))

    def test_database_connection_errors(self, record_repository, mock_db_connection):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.execute.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception) as exc_info:
            getattr(record_repository, "get_by_id")(*(1,))
        
        assert "Database connection failed" in str(exc_info.value)

    def test_missing_cursor_description(self, record_repository, mock_db_connection):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.fetchone.return_value = (1, "Article", "PubMed")
        mock_cursor.description = None
        result = record_repository.get_by_id(1)
        assert result is None

    def test_empty_cursor_description(self, record_repository, mock_db_connection):
        _, _, mock_cursor = mock_db_connection
        
        mock_cursor.fetchone.return_value = (1, "Article", "PubMed")
        mock_cursor.description = []
        result = record_repository.get_by_id(1)
        assert result is None
