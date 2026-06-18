from __future__ import annotations

import json
import os
from dataclasses import dataclass

import pandas as pd
from openai import OpenAI

from src.agents.planner_agent import AnalysisPlan
from src.config import load_env_file
from src.prompt_loader import load_prompt


@dataclass(frozen=True)
class InsightReport:
    headline: str
    summary: str
    observations: list[str]
    caveats: list[str]
    follow_up_questions: list[str]


class InsightsAgent:
    def __init__(self, model: str | None = None):
        load_env_file()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Export it before running insights."
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(
        self,
        plan: AnalysisPlan,
        result: pd.DataFrame,
        sql: str,
        question: str,
        validation_notes: list[str] | None = None,
        repair_messages: list[str] | None = None,
    ) -> InsightReport:
        table_sample = result.head(30).to_markdown(index=False)

        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": self._system_prompt()},
                {
                    "role": "user",
                    "content": f"""
User question:
{question}

Generated SQL:
{sql}

Planner metadata:
- intent: {plan.intent}
- metric: {plan.metric}
- chart_type: {plan.chart_type}
- x_column: {plan.x_column}
- y_column: {plan.y_column}
- series_column: {plan.series_column}

Validation notes:
{validation_notes or []}

Repair messages:
{repair_messages or []}

Result table sample:
{table_sample}

Write an insight report grounded only in the table above.
""",
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "air_quality_insight_report",
                    "strict": True,
                    "schema": self._insight_schema(),
                }
            },
        )

        payload = json.loads(response.output_text)
        return InsightReport(**payload)

    def _system_prompt(self) -> str:
        return load_prompt("insights/system.txt")

    def _insight_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "headline": {"type": "string"},
                "summary": {"type": "string"},
                "observations": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "caveats": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "follow_up_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "headline",
                "summary",
                "observations",
                "caveats",
                "follow_up_questions",
            ],
            "additionalProperties": False,
        }
