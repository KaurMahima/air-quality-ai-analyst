from __future__ import annotations

from pathlib import Path

import duckdb


class DuckDBTool:

    def __init__(
        self,
        db_path: str | Path = "warehouse/air_quality.duckdb",
        read_only: bool = True,
    ):
        self.db_path = Path(db_path)
        if read_only and not self.db_path.exists():
            raise FileNotFoundError(
                f"DuckDB warehouse not found: {self.db_path}. "
                "Run `python ingestion/load_data.py` first."
            )

        self.conn = duckdb.connect(str(self.db_path), read_only=read_only)

    def query(self, sql: str, params: list | tuple | None = None):
        return self.conn.execute(sql, params or []).fetchdf()

    def tables(self) -> list[str]:
        rows = self.conn.execute("SHOW TABLES").fetchall()
        return [row[0] for row in rows]

    def schema_context(self) -> str:
        parts: list[str] = []
        for table in self.tables():
            columns = self.conn.execute(f"DESCRIBE {table}").fetchall()
            column_text = ", ".join(
                f"{name} {dtype}" for name, dtype, *_ in columns
            )
            parts.append(f"{table}: {column_text}")
        return "\n".join(parts)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "DuckDBTool":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
