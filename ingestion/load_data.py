from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


DEFAULT_RAW_DIR = Path("data/raw")
DEFAULT_DB_PATH = Path("warehouse/air_quality.duckdb")

DATASET_FILES = {
    "city_day.csv": "city_day",
    "city_hour.csv": "city_hour",
    "station_day.csv": "station_day",
    "station_hour.csv": "station_hour",
    "stations.csv": "stations",
}


def load_csvs(raw_dir: Path, db_path: Path) -> list[str]:
    raw_dir = raw_dir.expanduser().resolve()
    db_path = db_path.expanduser().resolve()

    if not raw_dir.exists():
        raise FileNotFoundError(
            f"Raw data directory not found: {raw_dir}. "
            "Download the Kaggle CSV files into data/raw first."
        )

    db_path.parent.mkdir(parents=True, exist_ok=True)

    loaded_tables: list[str] = []
    with duckdb.connect(str(db_path)) as conn:
        for file_name, table_name in DATASET_FILES.items():
            csv_path = raw_dir / file_name
            if not csv_path.exists():
                continue

            conn.execute(
                f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT *
                FROM read_csv_auto(?, header = true, ignore_errors = true)
                """,
                [str(csv_path)],
            )
            loaded_tables.append(table_name)

        if not loaded_tables:
            expected = ", ".join(DATASET_FILES)
            raise FileNotFoundError(
                f"No Kaggle CSV files found in {raw_dir}. Expected one of: {expected}"
            )

    return loaded_tables


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load Kaggle India air quality CSV files into DuckDB."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DEFAULT_RAW_DIR,
        help="Directory containing downloaded Kaggle CSV files.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="DuckDB database path to create or replace tables in.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    loaded_tables = load_csvs(args.raw_dir, args.db_path)

    print(f"Loaded {len(loaded_tables)} table(s) into {args.db_path}:")
    for table_name in loaded_tables:
        print(f"- {table_name}")


if __name__ == "__main__":
    main()
