from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from nyc_taxi_trip_explorer.data import InvalidDateRangeError, TripAggregates


@dataclass(frozen=True)
class AppState:
    message_level: str | None = None
    message: str | None = None


def validate_date_selection(selection: Any) -> tuple[date | None, date | None]:
    if selection in (None, (), []):
        return None, None

    if isinstance(selection, tuple) and len(selection) == 2:
        start_date, end_date = selection
    else:
        start_date = selection
        end_date = selection

    if start_date is None and end_date is None:
        return None, None
    if start_date is None or end_date is None:
        raise InvalidDateRangeError("Please select both a start date and an end date.")
    if start_date > end_date:
        raise InvalidDateRangeError("Start date must be on or before end date.")
    return start_date, end_date


def build_app_state(result: TripAggregates | None, error: str | None = None) -> AppState:
    if error:
        return AppState(message_level="error", message=error)
    if result is None:
        return AppState()
    if result.trip_count == 0:
        return AppState(
            message_level="warning",
            message="No trips found for the selected date range.",
        )
    return AppState()


def render_state_message(st, state: AppState) -> None:
    if not state.message_level or not state.message:
        return
    getattr(st, state.message_level)(state.message)


def render_sidebar(st):
    st.sidebar.header("Filters")
    selection = st.sidebar.date_input(
        "Trip pickup date range",
        value=(),
        help="Choose a start and end date to reload the charts.",
    )
    st.sidebar.caption("Leave the picker empty to load the default, unfiltered view.")
    return selection


def chart_panels(st, result: TripAggregates) -> None:
    if result.trip_count == 0:
        st.info("No trip data is available for the selected date range.")
        return

    day_column, hour_column = st.columns(2)
    with day_column:
        st.subheader("Trips by day")
        st.bar_chart(result.daily, x="pickup_date", y="trip_count", use_container_width=True)

    with hour_column:
        st.subheader("Trips by hour")
        st.bar_chart(result.hourly, x="pickup_hour", y="trip_count", use_container_width=True)
