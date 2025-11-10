import pytest
from datetime import datetime
from psycopg import sql

from src.repositories.sqlbuilder import SQLBuilder


class TestSQLBuilder:
    
    @pytest.fixture
    def table_name(self):
        return "test_table"

    @pytest.fixture
    def sql_builder(self, table_name):
        return SQLBuilder(table_name)

    @pytest.mark.parametrize("fields", [
        set(),
        {"name"},
        {"name", "email"},
        {"id", "name", "email", "created_at"},
        {"field1", "field2", "field3", "field4", "field5"},
        set(), 
    ])
    def test_allow_fields_single_call(self, sql_builder, fields):
        result = sql_builder.allow_fields(fields)
        
        assert result is sql_builder
        assert sql_builder.allowed_fields == fields

    @pytest.mark.parametrize("initial_fields,additional_fields,expected_fields", [
        ({"name"}, {"email"}, {"name", "email"}),
        ({"id", "name"}, {"email", "created_at"}, {"id", "name", "email", "created_at"}),
        ({"field1"}, {"field1", "field2"}, {"field1", "field2"}),  # Duplicate handling
        (set(), {"name", "email"}, {"name", "email"}),
        ({"a", "b"}, set(), {"a", "b"}),
    ])
    def test_allow_fields_multiple_calls(self, sql_builder, initial_fields, additional_fields, expected_fields):
        sql_builder.allow_fields(initial_fields)
        sql_builder.allow_fields(additional_fields)
        
        assert sql_builder.allowed_fields == expected_fields

    @pytest.mark.parametrize("data,allowed_fields", [
        ({"name": "name"}, {"name"}),
        ({"name": "name", "email": "name@example.com"}, {"name", "email"}),
        ({"id": 1, "name": "name", "age": 30}, {"id", "name", "age"}),
        ({}, set()),  # Empty data
    ])
    def test_build_insert_valid_data(self, sql_builder, data, allowed_fields):
        sql_builder.allow_fields(allowed_fields)
        
        query, values = sql_builder.build_insert(data)
        
        assert isinstance(query, sql.Composed)
        
        assert isinstance(values, tuple)
        assert values == tuple(data.values())
        
        query_str = query.as_string(None)
        assert f'INSERT INTO "{sql_builder.table_name}"' in query_str or f"INSERT INTO {sql_builder.table_name}" in query_str
        assert "RETURNING id" in query_str
        
        if data:
            for column in data.keys():
                assert f'"{column}"' in query_str or column in query_str

    @pytest.mark.parametrize("data,allowed_fields,unknown_fields", [
        ({"name": "name", "invalid": "field"}, {"name"}, {"invalid"}),
        ({"name": "name", "email": "name@example.com"}, {"name"}, {"email"}),
        ({"unknown1": "value1", "unknown2": "value2"}, set(), {"unknown1", "unknown2"}),
        ({"valid": "field", "invalid1": "bad", "invalid2": "bad"}, {"valid"}, {"invalid1", "invalid2"}),
    ])
    def test_build_insert_unknown_fields(self, sql_builder, data, allowed_fields, unknown_fields):
        sql_builder.allow_fields(allowed_fields)
        
        with pytest.raises(ValueError) as exc_info:
            sql_builder.build_insert(data)
        
        error_message = str(exc_info.value)
        assert "Unknown fields:" in error_message
        for field in unknown_fields:
            assert field in error_message

    @pytest.mark.parametrize("data,table_name", [
        ({"name": "name"}, "authors"),
        ({"title": "Test Article"}, "articles"),
        ({"record_type": "Article"}, "records"),
        ({"field": "value"}, "test_table_123"),
    ])
    def test_build_insert_table_names(self, data, table_name):
        builder = SQLBuilder(table_name)
        builder.allow_fields(set(data.keys()))
        
        query, _ = builder.build_insert(data)
        
        query_str = query.as_string(None)
        assert f'INSERT INTO "{table_name}"' in query_str or f"INSERT INTO {table_name}" in query_str

    @pytest.mark.parametrize("data,id_value,allowed_fields", [
        ({"name": "name"}, 1, {"name"}),
        ({"name": "name", "email": "name@example.com"}, 42, {"name", "email"}),
        ({"title": "Test", "status": "published"}, 100, {"title", "status"}),
        ({}, 1, set()), 
    ])
    def test_build_update_valid_data(self, sql_builder, data, id_value, allowed_fields):
        sql_builder.allow_fields(allowed_fields | {"id"}) 
        
        query, values = sql_builder.build_update(data, id_value)
        
        assert isinstance(query, sql.Composed)
        
        assert isinstance(values, tuple)
        expected_values = (*tuple(data.values()), id_value)
        assert values == expected_values
        
        query_str = query.as_string(None)
        assert f"UPDATE {sql_builder.table_name} SET" in query_str or f'UPDATE "{sql_builder.table_name}" SET' in query_str
        assert "WHERE id = %s" in query_str or 'WHERE "id" = %s' in query_str
        
        if data:
            for column in data.keys():
                assert f"{column} = %s" in query_str or f'"{column}" = %s' in query_str

    @pytest.mark.parametrize("data,id_value,where_column,allowed_fields", [
        ({"name": "name"}, 1, "uuid", {"name", "uuid"}),
        ({"status": "updated"}, 42, "user_id", {"status", "user_id"}),
        ({"title": "New Title"}, 100, "article_id", {"title", "article_id"}),
    ])
    def test_build_update_custom_where(self, sql_builder, data, id_value, where_column, allowed_fields):
        sql_builder.allow_fields(allowed_fields)
        
        query, _ = sql_builder.build_update(data, id_value, where_column)
        
        query_str = query.as_string(None)
        assert f"WHERE {where_column} = %s" in query_str or f'WHERE "{where_column}" = %s' in query_str
        assert "WHERE id = %s" not in query_str and 'WHERE "id" = %s' not in query_str

    def test_build_update_by_id(self, sql_builder):
        data = {"name": "name"}
        sql_builder.allow_fields({"name"})  
        
        query, _ = sql_builder.build_update(data, 1, "id")
        
        query_str = query.as_string(None)
        assert "WHERE id = %s" in query_str or 'WHERE "id" = %s' in query_str

    @pytest.mark.parametrize("data,allowed_fields,unknown_fields", [
        ({"name": "name", "invalid": "field"}, {"name"}, {"invalid"}),
        ({"valid": "ok", "bad1": "no", "bad2": "no"}, {"valid"}, {"bad1", "bad2"}),
        ({"unknown": "field"}, set(), {"unknown"}),
    ])
    def test_build_update_unknown_fields(self, sql_builder, data, allowed_fields, unknown_fields):
        sql_builder.allow_fields(allowed_fields)
        
        with pytest.raises(ValueError) as exc_info:
            sql_builder.build_update(data, 1)
        
        error_message = str(exc_info.value)
        assert "Unknown fields:" in error_message
        for field in unknown_fields:
            assert field in error_message

    @pytest.mark.parametrize("where_column", [
        "invalid_column",
        "not_allowed", 
        "missing_field",
    ])
    def test_build_update_invalid_where_column(self, sql_builder, where_column):
        data = {"name": "name"}
        sql_builder.allow_fields({"name"})
        
        with pytest.raises(ValueError) as exc_info:
            sql_builder.build_update(data, 1, where_column)
        
        error_message = str(exc_info.value)
        assert f"Invalid where column: {where_column}" in error_message


    def test_sql_injection_protection(self, sql_builder):
        """Test that SQL injection attempts are properly handled."""
        malicious_table_name = "authors; DROP TABLE authors; --"
        malicious_column = "authors'; DROP TABLE authors; --"
        
        builder = SQLBuilder(malicious_table_name)
        builder.allow_fields({malicious_column})
        
        data = {malicious_column: "safe_value"}
        
        query, values = builder.build_insert(data)
        
        assert isinstance(query, sql.Composed)
        assert values == ("safe_value",)

    def test_empty_data_insert(self, sql_builder):
        sql_builder.allow_fields(set())
        
        query, values = sql_builder.build_insert({})
        
        query_str = query.as_string(None)
        assert f"INSERT INTO {sql_builder.table_name}" in query_str or f'INSERT INTO "{sql_builder.table_name}"' in query_str
        assert "VALUES ()" in query_str
        assert "RETURNING id" in query_str
        assert values == ()

    def test_empty_data_update(self, sql_builder):
        sql_builder.allow_fields(set())
        
        query, values = sql_builder.build_update({}, 1)
        
        query_str = query.as_string(None)
        assert f"UPDATE {sql_builder.table_name} SET" in query_str or f'UPDATE "{sql_builder.table_name}" SET' in query_str
        assert "WHERE id = %s" in query_str or 'WHERE "id" = %s' in query_str
        assert values == (1,)