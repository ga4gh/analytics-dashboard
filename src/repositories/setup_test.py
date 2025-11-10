import pytest
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager

from src.repositories.setup import DatabaseConnection


class TestDatabaseConnection:
    
    @pytest.fixture
    def connection_url(self):
        return "postgresql://user:pass@localhost:5432/testdb"

    @pytest.fixture
    def mock_connection_pool(self):
        return Mock()

    @pytest.fixture
    def mock_connection(self):
        return Mock()

    @pytest.mark.parametrize("connection_url,min_size,max_size", [
        ("postgresql://user:pass@localhost:5432/testdb", 1, 10),
        ("postgresql://admin:secret@db.example.com:5432/proddb", 5, 20),
        ("postgresql://test:test@127.0.0.1:5432/devdb", 2, 15),
        ("postgresql://analytics:analytics@analytics-db:5432/analytics", 3, 25),
    ])
    def test_init_with_parameters(self, connection_url, min_size, max_size):
        db_conn = DatabaseConnection(connection_url, min_size, max_size)
        
        assert db_conn.connection_url == connection_url
        assert db_conn.min_size == min_size
        assert db_conn.max_size == max_size
        assert db_conn.pool is None

    @pytest.mark.parametrize("connection_url", [
        "postgresql://user:pass@localhost:5432/testdb",
        "postgresql://admin:secret@db.example.com:5432/proddb",
        "postgresql://test@127.0.0.1:5432/devdb",
    ])
    def test_init_with_defaults(self, connection_url):
        db_conn = DatabaseConnection(connection_url)
        
        assert db_conn.connection_url == connection_url
        assert db_conn.min_size == 1
        assert db_conn.max_size == 10
        assert db_conn.pool is None

    @pytest.mark.parametrize("connection_url,min_size,max_size", [
        ("postgresql://user:pass@localhost:5432/testdb", 1, 10),
        ("postgresql://admin:secret@db.example.com:5432/proddb", 5, 20),
        ("postgresql://test:test@127.0.0.1:5432/devdb", 2, 15),
    ])
    @patch('src.repositories.setup.ConnectionPool')
    def test_connect_success(self, mock_connection_pool_class, connection_url, min_size, max_size):
        mock_pool_instance = Mock()
        mock_connection_pool_class.return_value = mock_pool_instance
        
        db_conn = DatabaseConnection(connection_url, min_size, max_size)
        db_conn.connect()
        
        mock_connection_pool_class.assert_called_once_with(
            conninfo=connection_url,
            min_size=min_size,
            max_size=max_size
        )
        assert db_conn.pool == mock_pool_instance

    @pytest.mark.parametrize("connection_error", [
        Exception("Connection failed: Invalid credentials"),
        RuntimeError("Database server unreachable"),
        ValueError("Invalid connection string format"),
        ConnectionError("Network timeout"),
    ])
    @patch('src.repositories.setup.ConnectionPool')
    def test_connect_errors(self, mock_connection_pool_class, connection_url, connection_error):
        mock_connection_pool_class.side_effect = connection_error
        
        db_conn = DatabaseConnection(connection_url)
        
        with pytest.raises(type(connection_error)) as exc_info:
            db_conn.connect()
        
        assert str(exc_info.value) == str(connection_error)
        assert db_conn.pool is None

    def test_disconnect_with_pool(self, connection_url):
        mock_pool = Mock()
        
        db_conn = DatabaseConnection(connection_url)
        db_conn.pool = mock_pool
        
        db_conn.disconnect()
        
        mock_pool.close.assert_called_once()

    def test_disconnect_without_pool(self, connection_url):
        db_conn = DatabaseConnection(connection_url)
        
        db_conn.disconnect()
        
        assert db_conn.pool is None

    @pytest.mark.parametrize("pool_state", [
        None,
        Mock(),
    ])
    def test_disconnect_pool_states(self, connection_url, pool_state):
        db_conn = DatabaseConnection(connection_url)
        db_conn.pool = pool_state
        
        db_conn.disconnect()
        
        if pool_state:
            pool_state.close.assert_called_once()

    @patch('src.repositories.setup.ConnectionPool')
    def test_get_connection_success(self, mock_connection_pool_class, connection_url):
        mock_pool = Mock()
        mock_conn = Mock()
        mock_connection_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        
        db_conn = DatabaseConnection(connection_url)
        db_conn.connect()
        
        with db_conn.get_connection() as conn:
            assert conn == mock_conn
        
        mock_pool.getconn.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)

    def test_get_connection_without_pool(self, connection_url):
        db_conn = DatabaseConnection(connection_url)
        
        with pytest.raises(RuntimeError) as exc_info:
            with db_conn.get_connection():
                pass
        
        assert "Database not connected. Call connect() first." in str(exc_info.value)

    @pytest.mark.parametrize("pool_error", [
        Exception("Pool exhausted"),
        RuntimeError("Connection timeout"),
        ValueError("Invalid connection state"),
    ])
    @patch('src.repositories.setup.ConnectionPool')
    def test_get_connection_pool_errors(self, mock_connection_pool_class, connection_url, pool_error):
        mock_pool = Mock()
        mock_connection_pool_class.return_value = mock_pool
        mock_pool.getconn.side_effect = pool_error
        
        db_conn = DatabaseConnection(connection_url)
        db_conn.connect()
        
        with pytest.raises(type(pool_error)) as exc_info:
            with db_conn.get_connection():
                pass
        
        assert str(exc_info.value) == str(pool_error)
        mock_pool.putconn.assert_not_called()

    @patch('src.repositories.setup.ConnectionPool')
    def test_get_connection_context_manager_cleanup(self, mock_connection_pool_class, connection_url):
        mock_pool = Mock()
        mock_conn = Mock()
        mock_connection_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        
        db_conn = DatabaseConnection(connection_url)
        db_conn.connect()
        
        with pytest.raises(ValueError):
            with db_conn.get_connection() as conn:
                assert conn == mock_conn
                raise ValueError("Test exception")
        
        mock_pool.getconn.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)