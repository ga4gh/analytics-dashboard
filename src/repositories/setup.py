from contextlib import contextmanager
from typing import Optional
from psycopg_pool import ConnectionPool

class DatabaseConnection:
    def __init__(self, connection_url: str, min_size: int = 1, max_size: int = 10):
        self.connection_url = connection_url
        self.pool: Optional[ConnectionPool] = None
        self.min_size = min_size
        self.max_size = max_size

    def connect(self):
        self.pool = ConnectionPool(
            conninfo=self.connection_url,
            min_size=self.min_size,
            max_size=self.max_size,
        )

    def disconnect(self):
        if self.pool:
            self.pool.closeall()

    @contextmanager
    def get_connection(self):
        if not self.pool:
            raise RuntimeError("Database not connected. Call connect() first.")

        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
