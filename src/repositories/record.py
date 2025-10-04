from src.models.record import Record as RecordModel

from .setup import DatabaseConnection
from .sqlbuilder import SQLBuilder


class Record:
    def __init__(self, db: DatabaseConnection, sql_builder: SQLBuilder) -> None:
        self.db = db
        self.sql_builder = sql_builder

    def insert(self, record: RecordModel) -> int:
        data = record.model_dump(exclude={"id"})
        query, values = self.sql_builder.build_insert(data)

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, values)
                record_id = cur.fetchone()[0] 
                conn.commit()
                return record_id

    def update(self, record: RecordModel) -> None:
        data = record.model_dump(exclude={"id"})
        query, values = self.sql_builder.build_update(data, record.id, "id")

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def get_by_id(self, id: int) -> RecordModel | None:
        query = "SELECT * FROM records WHERE id = %s"

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, (id,))
                row = cur.fetchone()

                if row and cur.description:
                    columns = [desc[0] for desc in cur.description]
                    data = dict(zip(columns, row, strict=False))
                    return RecordModel(**data)
                return None