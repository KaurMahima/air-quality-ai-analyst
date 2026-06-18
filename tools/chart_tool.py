from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("outputs/.matplotlib").resolve()))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("outputs/.cache").resolve()))
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import pandas as pd


class ChartTool:
    def __init__(self, output_dir: str | Path = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_chart(
        self,
        data: pd.DataFrame,
        chart_type: str,
        x_col: str,
        y_col: str,
        title: str,
        series_col: str = "",
        file_name: str = "agent_chart.png",
    ) -> Path:
        if chart_type == "line":
            return self.line_chart(data, x_col, y_col, title, series_col, file_name)
        if chart_type == "heatmap":
            return self.heatmap(data, x_col, y_col, title, series_col, file_name)
        if chart_type == "bar":
            return self.ranked_bar_chart(data, x_col, y_col, title, file_name)
        return self.table_output(data, file_name.replace(".png", ".csv"))

    def ranked_bar_chart(
        self,
        data: pd.DataFrame,
        label_col: str,
        value_col: str,
        title: str,
        file_name: str = "worst_air_quality_cities.png",
    ) -> Path:
        chart_data = data.sort_values(value_col, ascending=True)
        output_path = self.output_dir / file_name

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(chart_data[label_col], chart_data[value_col], color="#b23a48")
        ax.set_title(title)
        ax.set_xlabel(value_col.replace("_", " ").title())
        ax.set_ylabel(label_col)
        ax.grid(axis="x", alpha=0.25)
        fig.tight_layout()
        fig.savefig(output_path, dpi=160)
        plt.close(fig)

        return output_path

    def line_chart(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        series_col: str = "",
        file_name: str = "agent_chart.png",
    ) -> Path:
        output_path = self.output_dir / file_name

        fig, ax = plt.subplots(figsize=(10, 6))
        chart_data = data.sort_values(x_col)
        if series_col and series_col in chart_data.columns:
            for series_name, group in chart_data.groupby(series_col):
                ax.plot(group[x_col], group[y_col], marker="o", label=str(series_name))
            ax.legend()
        else:
            ax.plot(chart_data[x_col], chart_data[y_col], marker="o")

        ax.set_title(title)
        ax.set_xlabel(x_col.replace("_", " ").title())
        ax.set_ylabel(y_col.replace("_", " ").title())
        ax.grid(alpha=0.25)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(output_path, dpi=160)
        plt.close(fig)

        return output_path

    def table_output(self, data: pd.DataFrame, file_name: str = "agent_result.csv") -> Path:
        output_path = self.output_dir / file_name
        data.to_csv(output_path, index=False)
        return output_path

    def heatmap(
        self,
        data: pd.DataFrame,
        x_col: str,
        value_col: str,
        title: str,
        series_col: str,
        file_name: str = "agent_chart.png",
    ) -> Path:
        output_path = self.output_dir / file_name
        pivot = data.pivot_table(
            index=series_col,
            columns=x_col,
            values=value_col,
            aggfunc="mean",
        )
        pivot = pivot.sort_index()

        fig_width = max(10, min(18, 0.7 * len(pivot.columns) + 5))
        fig_height = max(6, min(16, 0.35 * len(pivot.index) + 2))
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))

        image = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
        ax.set_title(title)
        ax.set_xlabel(x_col.replace("_", " ").title())
        ax.set_ylabel(series_col.replace("_", " ").title())
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels([str(column) for column in pivot.columns], rotation=45, ha="right")
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels([str(index) for index in pivot.index])
        colorbar = fig.colorbar(image, ax=ax)
        colorbar.set_label(value_col.replace("_", " ").title())
        fig.tight_layout()
        fig.savefig(output_path, dpi=160)
        plt.close(fig)

        return output_path
