# air-quality-ai-analyst

Agentic workflow for air quality data analysis.

See [docs/README.md](docs/README.md) for the architecture walkthrough, screenshots, example questions, and limitations.

## Dataset

Use the Kaggle dataset: [Air Quality Data in India (2015 - 2020)](https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india).

Download it into `data/raw/`:

```bash
mkdir -p data/raw
kaggle datasets download -d rohanrao/air-quality-data-in-india -p data/raw --unzip
```

The loader looks for these common files from the dataset:

- `city_day.csv`
- `city_hour.csv`
- `station_day.csv`
- `station_hour.csv`
- `stations.csv`

## Load Data

Create and activate the Conda environment:

```bash
conda env create -f environment.yml
conda activate air-quality
```

Then build the DuckDB warehouse:

```bash
python ingestion/load_data.py
```

By default, the database is written to `warehouse/air_quality.duckdb`.

## Full Agentic Workflow

Run the LLM planner -> SQL -> DuckDB -> validation -> visualize -> insights pipeline:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

```bash
python workflows/full_agentic_workflow.py "Which Indian city has the worst air quality?" --show-sql
python workflows/full_agentic_workflow.py "Compare Delhi and Mumbai PM2.5 in 2020." --show-sql
```

If the LLM generates invalid SQL, the workflow sends the DuckDB error back to the planner and asks it to repair the plan. By default it tries 2 repairs:

```bash
python workflows/full_agentic_workflow.py "Compare Delhi and Mumbai PM2.5 in 2020." --show-sql --max-repairs 2
```

The plots are saved under `outputs/`.
Each run also saves a local trace under `runs/` unless you pass `--no-log`.

## Dashboard

Run the Streamlit dashboard:

```bash
export OPENAI_API_KEY="your_api_key_here"
streamlit run dashboard.py
```
