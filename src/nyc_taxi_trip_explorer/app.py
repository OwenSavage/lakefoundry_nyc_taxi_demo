from __future__ import annotations

import streamlit as st

from nyc_taxi_trip_explorer.data import DataRetrievalError, InvalidDateRangeError, default_repository
from nyc_taxi_trip_explorer.ui import (
    build_app_state,
    chart_panels,
    render_sidebar,
    render_state_message,
    validate_date_selection,
)


def run_app(streamlit_module, repository) -> None:
    streamlit_module.set_page_config(page_title="NYC Taxi Trip Explorer", layout="wide")
    streamlit_module.title("NYC Taxi Trip Explorer")
    streamlit_module.caption(
        "Explore trip volume trends from samples.nyctaxi.trips by day and by hour."
    )

    selection = render_sidebar(streamlit_module)

    try:
        start_date, end_date = validate_date_selection(selection)
    except InvalidDateRangeError as exc:
        render_state_message(streamlit_module, build_app_state(None, error=str(exc)))
        return

    try:
        result = repository.load_trips(start_date=start_date, end_date=end_date)
    except (DataRetrievalError, RuntimeError) as exc:
        render_state_message(streamlit_module, build_app_state(None, error=str(exc)))
        return

    render_state_message(streamlit_module, build_app_state(result))
    streamlit_module.metric("Trips in selection", result.trip_count)
    chart_panels(streamlit_module, result)


def main() -> None:
    repository = default_repository()
    run_app(st, repository)


if __name__ == "__main__":
    main()
