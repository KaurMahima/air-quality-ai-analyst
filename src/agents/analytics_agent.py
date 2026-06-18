from __future__ import annotations

from pathlib import Path

from tools.duckdb_tool import DuckDBTool


class AirQualityAnalyticsAgent:
    def __init__(self, db_path: str | Path = "warehouse/air_quality.duckdb"):
        self.db_path = db_path

    def run_sql(self, sql: str):
        return self._query(sql)

    def _query(self, sql: str, params: list | None = None):
        with DuckDBTool(self.db_path) as db:
            return db.query(sql, params)
