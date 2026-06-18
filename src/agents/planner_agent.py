from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace

from openai import OpenAI

from src.config import load_env_file
from src.prompt_loader import load_prompt


@dataclass(frozen=True)
class AnalysisPlan:
    question: str
    intent: str
    sql: str
    metric: str
    chart_type: str
    chart_title: str
    x_column: str
    y_column: str
    series_column: str
    insight_instruction: str


class PlannerAgent:
    def __init__(self, model: str | None = None):
        load_env_file()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Export it before running the LLM planner."
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def plan(
        self,
        question: str,
        schema_context: str,
        result_limit: int = 10,
    ) -> AnalysisPlan:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": self._system_prompt()},
                {
                    "role": "user",
                    "content": f"""
User question:
{question}

DuckDB schema:
{schema_context}

Preferred result limit:
{result_limit}

Return a plan and exactly one DuckDB SELECT query.
""",
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "air_quality_sql_plan",
                    "strict": True,
                    "schema": self._plan_schema(),
                }
            },
        )

        payload = json.loads(response.output_text)
        return AnalysisPlan(**payload)

    def repair_plan(
        self,
        plan: AnalysisPlan,
        schema_context: str,
        error_message: str,
    ) -> AnalysisPlan:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": self._repair_prompt()},
                {
                    "role": "user",
                    "content": f"""
Original user question:
{plan.question}

DuckDB schema:
{schema_context}

Previous plan:
{json.dumps(plan.__dict__, indent=2)}

Failure message:
{error_message}

Return a corrected plan and exactly one corrected DuckDB SELECT query.
""",
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "air_quality_sql_repair_plan",
                    "strict": True,
                    "schema": self._plan_schema(),
                }
            },
        )

        payload = json.loads(response.output_text)
        return replace(plan, **payload)

    def _system_prompt(self) -> str:
        return load_prompt("planner/system.txt")

    def _repair_prompt(self) -> str:
        return load_prompt("planner/repair_system.txt")

    def _plan_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "intent": {"type": "string"},
                "sql": {"type": "string"},
                "metric": {"type": "string"},
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "heatmap", "table"],
                },
                "chart_title": {"type": "string"},
                "x_column": {"type": "string"},
                "y_column": {"type": "string"},
                "series_column": {"type": "string"},
                "insight_instruction": {"type": "string"},
            },
            "required": [
                "question",
                "intent",
                "sql",
                "metric",
                "chart_type",
                "chart_title",
                "x_column",
                "y_column",
                "series_column",
                "insight_instruction",
            ],
            "additionalProperties": False,
        }
