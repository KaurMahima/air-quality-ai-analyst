from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_env_file
from tools.duckdb_tool import DuckDBTool
from workflows.agentic_runner import run_agentic_analysis

load_env_file(PROJECT_ROOT / ".env")
logger = logging.getLogger(__name__)


def load_deployment_secrets() -> None:
    for key in ("OPENAI_API_KEY", "OPENAI_MODEL", "APP_ACCESS_CODE"):
        try:
            value = st.secrets.get(key)
        except Exception:
            value = None

        if value and key not in os.environ:
            os.environ[key] = str(value)


def require_access_code() -> None:
    expected_code = os.getenv("APP_ACCESS_CODE")
    if not expected_code:
        return

    provided_code = st.text_input("Access code", type="password")
    if provided_code != expected_code:
        st.info("Enter the access code to use this dashboard.")
        st.stop()


load_deployment_secrets()


DEFAULT_QUESTION = "Which Indian city has the worst air quality?"
EXAMPLE_QUESTIONS = [
    DEFAULT_QUESTION,
    "Compare Delhi and Mumbai PM2.5 in 2020 by month.",
    "Which cities had the highest average AQI in 2019?",
    "Show the monthly AQI trend for Kolkata.",
    "Which stations reported the most observations?",
]


st.set_page_config(
    page_title="Air Quality Analyst",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Air Quality Analyst")
require_access_code()

with st.sidebar:
    db_path = st.text_input("DuckDB path", value="warehouse/air_quality.duckdb")
    result_limit = st.number_input("Result limit", min_value=1, max_value=100, value=10)
    max_repairs = st.number_input("SQL repairs", min_value=0, max_value=5, value=2)
    st.divider()
    st.caption("Examples")
    for example in EXAMPLE_QUESTIONS:
        if st.button(example, use_container_width=True):
            st.session_state.question = example
    st.divider()
    api_key_ready = bool(os.getenv("OPENAI_API_KEY"))
    warehouse_ready = Path(db_path).exists()
    st.status("OpenAI key", state="complete" if api_key_ready else "error")
    st.status("Warehouse", state="complete" if warehouse_ready else "error")

if "question" not in st.session_state:
    st.session_state.question = DEFAULT_QUESTION

question = st.text_area(
    "Question",
    value=st.session_state.question,
    height=90,
)

run_clicked = st.button("Run Analysis", type="primary", use_container_width=False)

if run_clicked:
    st.session_state.question = question
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is not set in this terminal.")
    elif not Path(db_path).exists():
        st.error(f"DuckDB warehouse not found: {db_path}")
    else:
        with st.spinner("Planning SQL, running DuckDB, validating, and charting..."):
            try:
                st.session_state.run_result = run_agentic_analysis(
                    question,
                    db_path=db_path,
                    result_limit=int(result_limit),
                    max_repairs=int(max_repairs),
                    log_run=True,
                )
            except Exception:
                logger.exception("Dashboard analysis failed")
                st.error(
                    "The analysis could not be completed. Please try a simpler "
                    "question or check the app logs for details."
                )

run_result = st.session_state.get("run_result")

if run_result:
    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Intent", run_result.plan.intent)
    metric_2.metric("Metric", run_result.plan.metric)
    metric_3.metric("Chart", run_result.plan.chart_type)
    metric_4.metric("Repairs", run_result.repairs_used)
    if run_result.run_dir:
        st.caption(f"Run saved to: {run_result.run_dir}")

    st.subheader("Insight")
    st.write(run_result.report.headline)
    st.write(run_result.report.summary)
    st.markdown("**Observations**")
    for observation in run_result.report.observations:
        st.write(f"- {observation}")
    st.markdown("**Caveats**")
    for caveat in run_result.report.caveats:
        st.caption(caveat)
    st.markdown("**Follow-up questions**")
    for follow_up in run_result.report.follow_up_questions:
        st.write(f"- {follow_up}")

    left, right = st.columns([1.1, 1])
    with left:
        st.subheader("Result")
        st.dataframe(run_result.result, use_container_width=True, hide_index=True)
        st.download_button(
            "Download result CSV",
            data=run_result.result.to_csv(index=False),
            file_name="air_quality_result.csv",
            mime="text/csv",
        )
    with right:
        st.subheader("Chart")
        if run_result.chart_path.suffix == ".png":
            st.image(str(run_result.chart_path), use_container_width=True)
        else:
            st.download_button(
                "Download table",
                data=run_result.chart_path.read_bytes(),
                file_name=run_result.chart_path.name,
            )

    with st.expander("Generated SQL", expanded=True):
        st.caption("Generated by the planner agent and validated before execution.")
        st.code(run_result.sql.strip(), language="sql")

    with st.expander("Validation"):
        st.write(run_result.sql_validation.message)
        st.write(run_result.result_validation.message)
        st.write(run_result.chart_validation.message)
        if run_result.run_dir:
            st.write(f"Run log: {run_result.run_dir}")

    if run_result.repair_messages:
        with st.expander("Repair Loop"):
            for message in run_result.repair_messages:
                st.write(message)
else:
    with st.expander("Database Schema"):
        if Path(db_path).exists():
            with DuckDBTool(db_path) as db:
                st.code(db.schema_context())
        else:
            st.write("Warehouse is not loaded yet.")
