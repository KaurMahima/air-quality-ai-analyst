from __future__ import annotations

from dataclasses import dataclass
import re

import pandas as pd


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    message: str


class ValidationAgent:
    BLOCKED_SQL_KEYWORDS = {
        "alter",
        "attach",
        "copy",
        "create",
        "delete",
        "detach",
        "drop",
        "insert",
        "install",
        "load",
        "pragma",
        "update",
    }
    BLOCKED_SQL_PATTERNS = {
        "read_csv",
        "read_csv_auto",
        "read_json",
        "read_parquet",
    }

    def validate_sql(self, sql: str) -> ValidationResult:
        normalized = " ".join(sql.lower().strip().split())
        normalized_without_trailing_semicolon = normalized.rstrip(";").strip()

        if ";" in normalized_without_trailing_semicolon:
            return ValidationResult(False, "Only one SQL statement is allowed.")

        if not normalized.startswith("select"):
            return ValidationResult(False, "Only SELECT queries are allowed.")

        tokens = set(re.findall(r"[a-z_]+", normalized))
        blocked = sorted(
            keyword for keyword in self.BLOCKED_SQL_KEYWORDS if keyword in tokens
        )
        if blocked:
            return ValidationResult(
                False,
                f"Query contains blocked keyword(s): {', '.join(blocked)}.",
            )

        blocked_patterns = sorted(
            pattern for pattern in self.BLOCKED_SQL_PATTERNS if pattern in normalized
        )
        if blocked_patterns:
            return ValidationResult(
                False,
                f"Query contains blocked function(s): {', '.join(blocked_patterns)}.",
            )

        return ValidationResult(True, "SQL is read-only and safe to run.")

    def validate_results(self, result: pd.DataFrame) -> ValidationResult:
        if result.empty:
            return ValidationResult(False, "Query returned no rows.")

        return ValidationResult(
            True,
            f"Result has {len(result)} row(s) and {len(result.columns)} column(s).",
        )

    def validate_chart_columns(
        self,
        result: pd.DataFrame,
        chart_type: str,
        x_column: str,
        y_column: str,
        series_column: str = "",
    ) -> ValidationResult:
        if chart_type == "table":
            return ValidationResult(True, "Table output does not require chart columns.")

        required_columns = [x_column, y_column]
        if series_column:
            required_columns.append(series_column)

        missing = [column for column in required_columns if column not in result.columns]
        if missing:
            return ValidationResult(
                False,
                f"Chart references missing result column(s): {', '.join(missing)}.",
                )

        if chart_type == "heatmap":
            if not series_column:
                candidates = self._series_column_candidates(result, x_column, y_column)
                suggestion = f" Candidate series columns: {', '.join(candidates)}." if candidates else ""
                return ValidationResult(
                    False,
                    "Heatmap requires series_column for the row/category dimension."
                    + suggestion,
                )
            return ValidationResult(True, "Heatmap columns exist in the result.")

        if chart_type == "line" and result[x_column].duplicated().any():
            if not series_column:
                candidates = self._series_column_candidates(result, x_column, y_column)
                suggestion = f" Candidate series columns: {', '.join(candidates)}." if candidates else ""
                return ValidationResult(
                    False,
                    "Line chart has repeated x-values but no series_column. "
                    "Set series_column to the grouping column so separate lines are drawn."
                    + suggestion,
                )
            series_count = result[series_column].nunique(dropna=True)
            if series_count > 12:
                return ValidationResult(
                    False,
                    f"Line chart has {series_count} series, which is too crowded. "
                    "Repair the plan to use chart_type heatmap with x_column as the "
                    "time bucket, series_column as the city/station/category, and "
                    "y_column as the numeric metric.",
                )

        return ValidationResult(True, "Chart columns exist in the result.")

    def _series_column_candidates(
        self,
        result: pd.DataFrame,
        x_column: str,
        y_column: str,
    ) -> list[str]:
        candidates = []
        for column in result.columns:
            if column in {x_column, y_column}:
                continue
            if (
                pd.api.types.is_object_dtype(result[column])
                or pd.api.types.is_string_dtype(result[column])
                or pd.api.types.is_categorical_dtype(result[column])
            ):
                candidates.append(column)
        return candidates
