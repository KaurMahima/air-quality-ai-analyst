from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import duckdb
import pandas as pd

from src.agents.analytics_agent import AirQualityAnalyticsAgent
from src.agents.insights_agent import InsightReport, InsightsAgent
from src.agents.planner_agent import AnalysisPlan, PlannerAgent
from src.agents.validation_agent import ValidationResult, ValidationAgent
from tools.chart_tool import ChartTool
from tools.duckdb_tool import DuckDBTool
from tools.run_logger import RunLogger


@dataclass(frozen=True)
class AgentRunResult:
    plan: AnalysisPlan
    sql: str
    result: pd.DataFrame
    chart_path: Path
    report: InsightReport
    sql_validation: ValidationResult
    result_validation: ValidationResult
    chart_validation: ValidationResult
    repairs_used: int
    repair_messages: list[str]
    run_dir: Path | None


def run_agentic_analysis(
    question: str,
    db_path: str | Path = "warehouse/air_quality.duckdb",
    result_limit: int = 10,
    max_repairs: int = 2,
    log_run: bool = True,
) -> AgentRunResult:
    planner = PlannerAgent()
    analytics = AirQualityAnalyticsAgent(db_path)
    validator = ValidationAgent()
    chart_tool = ChartTool()
    insights = InsightsAgent()

    with DuckDBTool(db_path) as db:
        schema_context = db.schema_context()

    plan = planner.plan(question, schema_context, result_limit=result_limit)
    repairs_used = 0
    repair_messages: list[str] = []

    while True:
        sql = plan.sql
        try:
            sql_validation = validator.validate_sql(sql)
            if not sql_validation.passed:
                raise ValueError(sql_validation.message)

            result = analytics.run_sql(sql)
            result_validation = validator.validate_results(result)
            if not result_validation.passed:
                raise ValueError(result_validation.message)

            chart_validation = validator.validate_chart_columns(
                result,
                plan.chart_type,
                plan.x_column,
                plan.y_column,
                plan.series_column,
            )
            if not chart_validation.passed:
                raise ValueError(chart_validation.message)

            break
        except (duckdb.Error, ValueError) as error:
            repairs_used += 1
            repair_message = f"Attempt {repairs_used}: {error}"
            repair_messages.append(repair_message)
            if repairs_used > max_repairs:
                raise RuntimeError(
                    "Agent could not repair the SQL after "
                    f"{max_repairs} attempt(s). Last error: {error}"
                ) from error

            plan = planner.repair_plan(plan, schema_context, str(error))

    chart_path = chart_tool.create_chart(
        result,
        chart_type=plan.chart_type,
        x_col=plan.x_column,
        y_col=plan.y_column,
        series_col=plan.series_column,
        title=plan.chart_title,
        file_name=_chart_file_name(plan.chart_title or question, plan.chart_type),
    )
    report = insights.generate(
        plan,
        result,
        sql=sql,
        question=question,
        validation_notes=[
            sql_validation.message,
            result_validation.message,
            chart_validation.message,
        ],
        repair_messages=repair_messages,
    )

    run_dir = None
    if log_run:
        run_dir = RunLogger().save_run(
            question=question,
            plan=plan,
            sql=sql,
            result=result,
            chart_path=chart_path,
            report=report,
            sql_validation=sql_validation,
            result_validation=result_validation,
            chart_validation=chart_validation,
            repairs_used=repairs_used,
            repair_messages=repair_messages,
        )

    return AgentRunResult(
        plan=plan,
        sql=sql,
        result=result,
        chart_path=chart_path,
        report=report,
        sql_validation=sql_validation,
        result_validation=result_validation,
        chart_validation=chart_validation,
        repairs_used=repairs_used,
        repair_messages=repair_messages,
        run_dir=run_dir,
    )


def _chart_file_name(title: str, chart_type: str) -> str:
    slug = _slugify(title)
    extension = "csv" if chart_type == "table" else "png"
    return f"{slug}.{extension}"


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    parts = [part for part in cleaned.split("-") if part]
    return "-".join(parts[:10]) or "air-quality-analysis"
