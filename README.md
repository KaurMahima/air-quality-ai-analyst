# air-quality-ai-analyst

Agentic air quality analyst for the Kaggle India air quality dataset. The system converts natural-language questions into DuckDB SQL, validates and repairs the SQL when needed, runs the query, creates a chart, and generates an analyst-style insight.

## Architecture

```text
User question
  -> Planner Agent
  -> SQL Validator
  -> DuckDB Tool
  -> Repair Loop
  -> Chart Tool
  -> Insights Agent
  -> CLI or Streamlit Dashboard
```

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

## Agent Workflow

1. The user asks a question in the CLI or dashboard.
2. `PlannerAgent` receives the question plus the live DuckDB schema.
3. The LLM returns structured JSON with intent, SQL, metric, chart type, and chart columns.
4. `ValidationAgent` checks that the SQL is read-only and safe.
5. `DuckDBTool` runs the SQL against `warehouse/air_quality.duckdb`.
6. If validation or DuckDB execution fails, the repair loop sends the error back to the LLM and retries.
7. `ChartTool` creates a bar, line, heatmap, or table artifact.
8. `InsightsAgent` uses the result table and metadata to write a grounded insight report.
9. `RunLogger` saves a trace of the run under `runs/`.

## Run Logs

Each successful CLI or dashboard run saves a trace directory:

```text
runs/
  20260616_145011_compare-delhi-and-mumbai-pm2-5/
    run.json
    result.csv
    compare-delhi-and-mumbai-pm2-5-in-2020.png
```

The JSON trace includes the user question, planner output, generated SQL, validation messages, repair attempts, insight report, and artifact paths. 

## Demo Artifact

See [Air Quality Analyst demo PDF](artifacts/air-quality-analyst-demo.pdf) for an example run showing the dashboard, generated SQL, chart, validation status, and insights.

## Dashboard

Run the Streamlit dashboard:

```bash
export OPENAI_API_KEY="your_api_key_here"
streamlit run dashboard.py
```

Then open:

The dashboard shows:

- the natural-language question
- generated SQL
- result table
- chart
- validation status
- repair messages
- LLM-generated insights

## Example Questions

```text
Which Indian city has the worst air quality?
Compare Delhi and Mumbai PM2.5 in 2020 by month.
Which cities had the highest average AQI in 2019?
Show the monthly AQI trend for Kolkata.
Which stations reported the most observations?
```

## Limitations

- The dataset ends in 2020.
- Reporting coverage varies by city and station.
- Rankings depend on the metric selected by the planner.
- Results reflect available observations, not necessarily complete exposure.
- The system is an analytical assistant, not a medical or regulatory decision tool.
