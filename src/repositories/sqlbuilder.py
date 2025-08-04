from psycopg import sql


class SQLBuilder:
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name
        self.allowed_fields = set()

    def allow_fields(self, fields: set) -> "SQLBuilder":
        self.allowed_fields.update(fields)
        return self

    def build_insert(self, data: dict[str, any]) -> tuple[sql.SQL, tuple]:
        # Validate fields
        unknown = set(data.keys()) - self.allowed_fields
        if unknown:
            error_msg = f"Unknown fields: {unknown}"
            raise ValueError(error_msg)

        columns = list(data.keys())
        values = tuple(data.values())

        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
              sql.Identifier(self.table_name),
              sql.SQL(", ").join(map(sql.Identifier, columns)),
              sql.SQL(", ").join(sql.Placeholder() * len(values))
          )

        return query, values

    def build_update(self, data: dict[str, any], id_value: int, where_column: str = "id") -> tuple[sql.SQL, tuple]:
        unknown = set(data.keys()) - self.allowed_fields
        if unknown:
            error_msg = f"Unknown fields: {unknown}"
            raise ValueError(error_msg)

        if where_column not in self.allowed_fields and where_column != "id":
              error_msg = f"Invalid where column: {where_column}"
              raise ValueError(error_msg)

        columns = list(data.keys())
        values = (*tuple(data.values()), id_value)

        set_clauses = sql.SQL(", ").join([
              sql.SQL("{} = {}").format(sql.Identifier(col), sql.Placeholder())
              for col in columns
          ])

        query = sql.SQL("UPDATE {} SET {} WHERE {} = {}").format(
            sql.Identifier(self.table_name),
            set_clauses,
            sql.Identifier(where_column),
            sql.Placeholder()
        )

        return query, values
