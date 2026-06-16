from __future__ import annotations

from datetime import date

import pandas as pd

from nyc_taxi_trip_explorer.data import InvalidDateRangeError, TripAggregates
from nyc_taxi_trip_explorer.ui import (
    AppState,
    build_app_state,
    chart_panels,
    validate_date_selection,
)


class RecordingStreamlit:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []
        self.subheaders: list[str] = []
        self.bar_charts: list[pd.DataFrame] = []
        self.columns_requested: list[int] = []

    def error(self, message: str) -> None:
        self.messages.append(("error", message))

    def warning(self, message: str) -> None:
        self.messages.append(("warning", message))

    def info(self, message: str) -> None:
        self.messages.append(("info", message))

    def columns(self, count: int):
        self.columns_requested.append(count)
        return [self, self]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def bar_chart(self, data: pd.DataFrame, x: str, y: str, use_container_width: bool = False) -> None:
        self.bar_charts.append(data.copy())


SAMPLE_AGGREGATES = TripAggregates(
    daily=pd.DataFrame(
        [
            {"pickup_date": date(2016, 2, 1), "trip_count": 2},
            {"pickup_date": date(2016, 2, 2), "trip_count": 1},
        ]
    ),
    hourly=pd.DataFrame(
        [
            {"pickup_hour": 8, "trip_count": 2},
            {"pickup_hour": 9, "trip_count": 1},
        ]
    ),
    trip_count=3,
)


def test_validate_date_selection_accepts_none_and_valid_ranges() -> None:
    assert validate_date_selection(None) == (None, None)
    assert validate_date_selection((date(2016, 2, 1), date(2016, 2, 3))) == (
        date(2016, 2, 1),
        date(2016, 2, 3),
    )


def test_validate_date_selection_rejects_invalid_ranges() -> None:
    try:
        validate_date_selection((date(2016, 2, 5), date(2016, 2, 1)))
    except InvalidDateRangeError:
        pass
    else:
        raise AssertionError("Expected InvalidDateRangeError")


def test_build_app_state_uses_warning_for_empty_results() -> None:
    empty = TripAggregates(
        daily=pd.DataFrame(columns=["pickup_date", "trip_count"]),
        hourly=pd.DataFrame(columns=["pickup_hour", "trip_count"]),
        trip_count=0,
    )

    state = build_app_state(empty)

    assert state.message_level == "warning"
    assert "No trips found" in state.message


def test_build_app_state_preserves_error_message() -> None:
    state = build_app_state(None, error="Warehouse request failed")

    assert state == AppState(message_level="error", message="Warehouse request failed")


def test_chart_panels_draw_two_charts_when_data_is_available() -> None:
    st = RecordingStreamlit()

    chart_panels(st, SAMPLE_AGGREGATES)

    assert st.columns_requested == [2]
    assert st.subheaders == ["Trips by day", "Trips by hour"]
    assert len(st.bar_charts) == 2


def test_chart_panels_show_info_message_for_empty_data() -> None:
    st = RecordingStreamlit()
    empty = TripAggregates(
        daily=pd.DataFrame(columns=["pickup_date", "trip_count"]),
        hourly=pd.DataFrame(columns=["pickup_hour", "trip_count"]),
        trip_count=0,
    )

    chart_panels(st, empty)

    assert ("info", "No trip data is available for the selected date range.") in st.messages
