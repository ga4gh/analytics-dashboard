from src.models.record import Record as RecordModel

from .setup import DatabaseConnection
from .sqlbuilder import SQLBuilder


class Record:
    def __init__(self, db: DatabaseConnection, table_name: str = "record") -> None:
        self.db = db
        self.table_name = table_name

    def create_record(self, record: RecordModel):
        data = record.model_dump(exclude={"id"})
        columns = list(data.keys())
        values = tuple(data.values())
        placeholders = ", ".join(["%s"] * len(values))
        query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print(query, values)    
                cur.execute(query, values)                           
                record_id = cur.fetchone()[0]  # Get the generated ID
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