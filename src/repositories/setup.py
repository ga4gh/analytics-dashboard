from collections.abc import Iterator
from contextlib import contextmanager

from psycopg import Connection
from psycopg_pool import ConnectionPool


class DatabaseConnection:
    def __init__(self, connection_url: str, min_size: int = 1, max_size: int = 10) -> None:
        self.connection_url = connection_url
        self.pool: ConnectionPool | None = None
        self.min_size = min_size
        self.max_size = max_size

    def connect(self) -> None:
        self.pool = ConnectionPool(
            conninfo=self.connection_url,
            min_size=self.min_size,
            max_size=self.max_size,
        )

    def disconnect(self) -> None:
        if self.pool:
            self.pool.close()

    @contextmanager
    def get_connection(self) -> Iterator[Connection]:
        if not self.pool:
            error_msg = "Database not connected. Call connect() first."
            raise RuntimeError(error_msg)

        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
