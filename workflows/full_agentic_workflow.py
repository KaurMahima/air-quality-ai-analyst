from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from workflows.agentic_runner import run_agentic_analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full air quality agent.")
    parser.add_argument(
        "question",
        nargs="?",
        default="Which Indian city has the worst air quality?",
        help="Natural-language air quality question.",
    )
    parser.add_argument("--limit", type=int, default=10, help="Rows to return.")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("warehouse/air_quality.duckdb"),
        help="DuckDB warehouse path.",
    )
    parser.add_argument(
        "--show-sql",
        action="store_true",
        help="Print generated SQL before the result.",
    )
    parser.add_argument(
        "--max-repairs",
        type=int,
        default=2,
        help="Number of LLM repair attempts after validation or SQL errors.",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Do not save a run trace under runs/.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    run = run_agentic_analysis(
        args.question,
        db_path=args.db_path,
        result_limit=args.limit,
        max_repairs=args.max_repairs,
        log_run=not args.no_log,
    )

    print("Planner Agent")
    print(f"- intent: {run.plan.intent}")
    print(f"- metric: {run.plan.metric}")
    print(f"- chart_type: {run.plan.chart_type}")
    print(f"- repairs_used: {run.repairs_used}")
    print()

    if run.repair_messages:
        print("Repair Loop")
        for message in run.repair_messages:
            print(f"- {message}")
        print()

    if args.show_sql:
        print("Generated SQL")
        print(run.sql.strip())
        print()

    print("DuckDB Result")
    print(run.result.to_string(index=False))
    print()

    print("Validation Agent")
    print(f"- SQL: {run.sql_validation.message}")
    print(f"- Result: {run.result_validation.message}")
    print(f"- Chart: {run.chart_validation.message}")
    print()

    print("Visualizer")
    print(f"- chart: {run.chart_path}")
    print()

    if run.run_dir:
        print("Run Log")
        print(f"- saved: {run.run_dir}")
        print()

    print("Insights Agent")
    print(f"- {run.report.headline}")
    print(f"- {run.report.summary}")
    print("- Observations:")
    for observation in run.report.observations:
        print(f"  - {observation}")
    print("- Caveats:")
    for caveat in run.report.caveats:
        print(f"  - {caveat}")
    print("- Follow-up questions:")
    for follow_up in run.report.follow_up_questions:
        print(f"  - {follow_up}")


if __name__ == "__main__":
    main()
