from src.models.animal import Animal

from .setup import DatabaseConnection
from .sqlbuilder import SQLBuilder


class Animals:
    def __init__(self, db: DatabaseConnection, sql_builder: SQLBuilder) -> None:
        self.db = db
        self.sql_builder = sql_builder

    def create_animal(self, animal: Animal) -> None:
        data = animal.model_dump(exclude={"id"})
        query, values = self.sql_builder.build_insert(data)

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def update_animal(self, animal: Animal) -> None:
        data = animal.model_dump(exclude={"id"})
        query, values = self.sql_builder.build_update(data, animal.id, "id")

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

    def get_animal_by_id(self, animal_id: int) -> Animal | None:
        query = "SELECT * FROM animals WHERE id = %s"

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, (animal_id,))
                row = cur.fetchone()

                if row:
                    columns = [desc[0] for desc in cur.description]
                    data = dict(zip(columns, row, strict=False))
                    return Animal(**data)
                return None

    def get_animal_by_name(self, name: str) -> list[Animal]:
        query = "SELECT * FROM animals WHERE name = %s"

        with self.db.get_connection() as conn, conn.cursor() as cur:
                cur.execute(query, (name,))
                rows = cur.fetchall()

                if rows:
                    columns = [desc[0] for desc in cur.description]
                    animals = []
                    for row in rows:
                        data = dict(zip(columns, row, strict=False))
                        animals.append(Animal(**data))
                    return animals
                return []
