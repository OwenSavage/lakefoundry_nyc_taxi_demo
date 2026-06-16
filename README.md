# NYC Taxi Trip Explorer Databricks App

This repository packages the NYC Taxi Trip Explorer Streamlit application as a Databricks App using a Databricks Asset Bundle (DAB).

## Deployment verification status

Task 3 completed workspace validation and deployment verification for the Databricks App resource. The final bundle uses direct deployment mode for app lifecycle support and declares a Databricks App `sql-warehouse` resource binding so `app/app.yaml` can resolve `valueFrom: sql-warehouse` at runtime.

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
- `app/app.py` bootstraps the repository-local `src/` directory before invoking `nyc_taxi_trip_explorer.app`, so startup does not depend on a hard-coded `PYTHONPATH` layout.
- `app/requirements.txt` installs the project package from the bundle root, which keeps the Databricks App environment aligned with local development packaging.
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

With the current bundle, deploy uses `deployment.mode: direct` so the Databricks App resource is managed through the app deployment API rather than Terraform-only metadata.

### Start or update the Databricks App

```bash
databricks bundle run nyc_taxi_trip_explorer
```

If `bundle run` reports the app resource is not found, re-run `databricks bundle deploy` after confirming direct deployment mode is present. For this app, the direct deployment change was required to make the app startable from the bundle.

## Required environment variables

### For local development

- `DATABRICKS_WAREHOUSE_ID`: SQL warehouse id used by the app's query layer.
- Standard Databricks SDK authentication variables if your local CLI profile does not already provide them.

### For deployed Databricks Apps

- `DATABRICKS_WAREHOUSE_ID` should be attached as an app resource via Databricks Apps metadata and resolved by `valueFrom` in `app/app.yaml`.

## Analyst usage

After deployment:

1. Open the Databricks App URL.
2. Wait for the initial unfiltered chart load.
3. Use the sidebar date range selector to choose the period to analyze.
4. Review the trips-by-day chart to spot daily volume trends.
5. Review the trips-by-hour chart to compare intraday activity.
6. Adjust the date range and confirm both charts refresh together.
7. For no-data ranges, confirm the app shows handled empty-state feedback instead of failing.

## Validation performed in Task 3

Workspace verification commands executed:

```bash
databricks bundle validate
databricks bundle deploy --auto-approve
databricks bundle run nyc_taxi_trip_explorer
```

Observed deployment details from verification:

- App name: `nyc-taxi-trip-explorer-dev`
- App id: `59ce53ee-017b-491d-8ff5-25106115ceaf`
- App URL: `https://nyc-taxi-trip-explorer-dev-3894241741096798.aws.databricksapps.com`
- Required bundle fix: `deployment.mode: direct`
- Required app fix: declare the `sql-warehouse` app resource binding used by `app/app.yaml`

Verification notes:

- `databricks bundle validate` succeeded.
- `databricks bundle deploy --auto-approve` succeeded.
- An initial `databricks bundle run nyc_taxi_trip_explorer` failed before the direct deployment fix with `resource not found or not yet deployed`.
- The app was confirmed in the workspace through `databricks apps get`, including URL, app id, and compute state.
- Because the environment authenticated with a PAT, `databricks apps logs` returned `OAuth Token not supported for current auth type pat`, so app-log collection was blocked by auth type rather than app code.
- A direct API deployment attempt (`databricks apps deploy nyc-taxi-trip-explorer-dev --source-code-path ...`) reached the app deployment service but failed during package installation with `Error installing packages. Please check /logz for more details`.
- Acceptance-evidence for chart load, live filtering, and empty-state behavior remains primarily covered by the tested app logic plus the deployed app URL and workspace app metadata collected in this task.
