# NYC Taxi Trip Explorer Databricks App

This repository packages the NYC Taxi Trip Explorer Streamlit application as a Databricks App using a Databricks Asset Bundle (DAB).

## Scope boundary for this task

This task adds bundle scaffolding, the Databricks App runtime wrapper, and usage documentation.

Deployment execution is intentionally **deferred to Task 3**. Reviewers should expect local packaging and validation readiness here, not workspace deploy/run evidence.

## Repository layout

- `src/nyc_taxi_trip_explorer/`: Streamlit application package created in Task 1.
- `app/`: Databricks App source directory used by the bundle.
- `resources/nyc_taxi_trip_explorer.app.yml`: Databricks App bundle resource.
- `databricks.yml`: bundle root configuration.

## Local development

### Prerequisites

- Python 3.11+
- Databricks CLI installed and authenticated for later deployment work
- Access to a Databricks SQL warehouse that can query `samples.nyctaxi.trips`

### Install dependencies

```bash
python -m pip install -e .[dev]
```

### Run the Streamlit app locally

Set the warehouse id for local data access:

```bash
export DATABRICKS_WAREHOUSE_ID=<your-sql-warehouse-id>
streamlit run src/nyc_taxi_trip_explorer/app.py
```

The app uses Databricks SDK environment-based authentication. Do not hardcode tokens or credentials in source files.

## Databricks App runtime configuration

The deployed app reads runtime settings from `app/app.yaml`.

- `DATABRICKS_WAREHOUSE_ID` is provided through `valueFrom: sql-warehouse` so the warehouse binding is managed by Databricks App metadata.
- `PYTHONPATH` includes `/app` and `/app/src` so the wrapper can import the packaged Python module.
- The Streamlit command binds to port `8080`, which matches Databricks Apps expectations.

## Bundle commands

These are the commands reviewers and operators should use once deployment work begins.

### Validate bundle locally

```bash
databricks bundle validate
```

### Deploy bundle

```bash
databricks bundle deploy
```

### Start or update the Databricks App

```bash
databricks bundle run nyc_taxi_trip_explorer
```

> For this task, deploy and run are documented only. Executing them is intentionally deferred to Task 3.

## Required environment variables

### For local development

- `DATABRICKS_WAREHOUSE_ID`: SQL warehouse id used by the app's query layer.
- Standard Databricks SDK authentication variables if your local CLI profile does not already provide them.

### For deployed Databricks Apps

- `DATABRICKS_WAREHOUSE_ID` should be attached as an app resource via Databricks Apps metadata and resolved by `valueFrom` in `app/app.yaml`.

## Analyst usage

After deployment in Task 3:

1. Open the Databricks App URL.
2. Use the sidebar date range selector to choose the period to analyze.
3. Review the trips-by-day chart to spot daily volume trends.
4. Review the trips-by-hour chart to compare intraday activity.
5. Adjust the date range and confirm both charts refresh together.

## Validation performed in this task

This task is limited to local packaging validation readiness.

Recommended checks for this phase:

```bash
pytest
databricks bundle validate
```

If bundle validation depends on workspace authentication in the current environment, that is acceptable to defer as long as the bundle files are ready for Task 3 execution.
