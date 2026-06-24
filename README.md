# NYC Taxi Trip Explorer Databricks App

This repository packages the NYC Taxi Trip Explorer Streamlit application as a Databricks App using a Databricks Asset Bundle (DAB).

## Repository layout

- `src/nyc_taxi_trip_explorer/`: application package for data access, UI helpers, and the Streamlit entrypoint.
- `app/`: Databricks App source directory, including `app.yaml` and deployment-time requirements.
- `resources/nyc_taxi_trip_explorer.app.yml`: Databricks App bundle resource definition.
- `databricks.yml`: bundle root configuration.
- `tests/`: unit and integration-style tests covering filter handling and user-facing states.

## Local development

### Prerequisites

- Python 3.11+
- Databricks CLI installed and authenticated for local validation or later deployment work
- Access to a Databricks SQL warehouse that can query `samples.nyctaxi.trips`

### Install dependencies

```bash
python -m pip install -e .[dev]
```

### Run the Streamlit app locally

Set the warehouse id used by the query layer, then start Streamlit:

```bash
export DATABRICKS_WAREHOUSE_ID=<your-sql-warehouse-id>
streamlit run src/nyc_taxi_trip_explorer/app.py
```

The app uses Databricks SDK environment-based authentication. Keep credentials in your Databricks CLI profile or standard SDK environment variables rather than hardcoding them in source.

### Run the relevant tests

```bash
pytest tests/test_app.py tests/test_data.py tests/test_ui.py
```

The current test suite covers the initial unfiltered load path, valid sidebar date filtering, invalid date handling, empty-result messaging, and backend failure handling.

## Databricks App runtime configuration

Runtime settings are defined in `app/app.yaml` and the bundle app resource.

- `app/app.yaml` starts Streamlit on port `8080`, which matches Databricks Apps expectations.
- `DATABRICKS_WAREHOUSE_ID` is resolved from `valueFrom: sql-warehouse`.
- `resources/nyc_taxi_trip_explorer.app.yml` declares the matching `sql-warehouse` app resource binding with `CAN_USE` permission and a concrete warehouse id for deployment.
- `app/requirements.txt` installs the packaged project from the bundle root so the deployed app matches the local package structure.

## Bundle validation and deployment flow

Task 2 is limited to tests and operator documentation, but these are the commands operators should use for this app:

```bash
databricks bundle validate
databricks bundle deploy
databricks bundle run nyc_taxi_trip_explorer
```

Use `bundle validate` to confirm bundle structure, `bundle deploy` to sync the Databricks App resource and source code, and `bundle run nyc_taxi_trip_explorer` to start or refresh the deployed app.

## Required configuration

### Local development

- `DATABRICKS_WAREHOUSE_ID`: required so the local app can query the SQL warehouse.
- Databricks SDK authentication via CLI profile or standard environment variables.

### Deployed Databricks App

- The deployed app expects the `sql-warehouse` app resource binding declared in `resources/nyc_taxi_trip_explorer.app.yml`.
- `app/app.yaml` reads `DATABRICKS_WAREHOUSE_ID` from that binding at runtime.

## Analyst usage

After the app starts:

1. Open the NYC Taxi Trip Explorer app.
2. Wait for the initial unfiltered charts to load.
3. Use the sidebar date picker to choose a valid start and end date.
4. Review the trips-by-day chart for daily volume changes.
5. Review the trips-by-hour chart for intraday distribution.
6. If the selected date range has no rows, expect the app to show handled empty-state messages.
7. If a date range is invalid or the backend query fails, expect the app to show an error message instead of crashing.

## Verification commands for this phase

For the tests-and-docs phase, use:

```bash
pytest tests/test_app.py tests/test_data.py tests/test_ui.py
```

Workspace deployment execution and final deployed URL verification are handled separately in Task 3.
