from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pandas as pd


class RunLogger:
    def __init__(self, output_dir: str | Path = "runs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_run(
        self,
        question: str,
        plan,
        sql: str,
        result: pd.DataFrame,
        chart_path: Path,
        report,
        sql_validation,
        result_validation,
        chart_validation,
        repairs_used: int,
        repair_messages: list[str],
    ) -> Path:
        run_dir = self._new_run_dir(question)
        run_dir.mkdir(parents=True, exist_ok=True)

        result_path = run_dir / "result.csv"
        result.to_csv(result_path, index=False)

        chart_copy_path = None
        if chart_path.exists():
            chart_copy_path = run_dir / chart_path.name
            shutil.copy2(chart_path, chart_copy_path)

        metadata = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "question": question,
            "plan": asdict(plan),
            "sql": sql,
            "validations": {
                "sql": asdict(sql_validation),
                "result": asdict(result_validation),
                "chart": asdict(chart_validation),
            },
            "repairs_used": repairs_used,
            "repair_messages": repair_messages,
            "insight": asdict(report),
            "chart_path": str(chart_path),
            "chart_copy_path": str(chart_copy_path) if chart_copy_path else None,
            "result_path": str(result_path),
        }

        metadata_path = run_dir / "run.json"
        metadata_path.write_text(json.dumps(metadata, indent=2, default=str))

        return run_dir

    def _new_run_dir(self, question: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{timestamp}_{self._slugify(question)}"

    def _slugify(self, text: str) -> str:
        cleaned = "".join(
            char.lower() if char.isalnum() else "-" for char in text.strip()
        )
        parts = [part for part in cleaned.split("-") if part]
        return "-".join(parts[:8]) or "run"
