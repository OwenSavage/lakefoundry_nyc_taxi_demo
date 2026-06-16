from __future__ import annotations

from datetime import date

import pandas as pd

from nyc_taxi_trip_explorer.data import InvalidDateRangeError, TripAggregates
from nyc_taxi_trip_explorer.app import run_app


class FakeSidebar:
    def __init__(self, selection):
        self.selection = selection
        self.headers: list[str] = []
        self.captions: list[str] = []

    def header(self, text: str) -> None:
        self.headers.append(text)

    def date_input(self, *args, **kwargs):
        return self.selection

    def caption(self, text: str) -> None:
        self.captions.append(text)


class FakeStreamlit:
    def __init__(self, selection):
        self.sidebar = FakeSidebar(selection)
        self.page_config: list[dict[str, str]] = []
        self.titles: list[str] = []
        self.captions: list[str] = []
        self.messages: list[tuple[str, str]] = []
        self.metrics: list[tuple[str, int]] = []
        self.columns_requested: list[int] = []
        self.subheaders: list[str] = []
        self.bar_charts: list[pd.DataFrame] = []

    def set_page_config(self, **kwargs) -> None:
        self.page_config.append(kwargs)

    def title(self, text: str) -> None:
        self.titles.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def error(self, message: str) -> None:
        self.messages.append(("error", message))

    def warning(self, message: str) -> None:
        self.messages.append(("warning", message))

    def info(self, message: str) -> None:
        self.messages.append(("info", message))

    def metric(self, label: str, value: int) -> None:
        self.metrics.append((label, value))

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


class RecordingRepository:
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls: list[tuple[date | None, date | None]] = []

    def load_trips(self, start_date=None, end_date=None):
        self.calls.append((start_date, end_date))
        if self.error is not None:
            raise self.error
        return self.result


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


def test_run_app_renders_title_metrics_and_charts() -> None:
    st = FakeStreamlit((date(2016, 2, 1), date(2016, 2, 2)))
    repository = RecordingRepository(result=SAMPLE_AGGREGATES)

    run_app(st, repository)

    assert st.page_config[0]["page_title"] == "NYC Taxi Trip Explorer"
    assert st.titles == ["NYC Taxi Trip Explorer"]
    assert repository.calls == [(date(2016, 2, 1), date(2016, 2, 2))]
    assert ("Trips in selection", 3) in st.metrics
    assert len(st.bar_charts) == 2


def test_run_app_handles_invalid_date_range_without_querying() -> None:
    st = FakeStreamlit((date(2016, 2, 5), date(2016, 2, 1)))
    repository = RecordingRepository(result=SAMPLE_AGGREGATES)

    run_app(st, repository)

    assert repository.calls == []
    assert any(level == "error" for level, _ in st.messages)


def test_run_app_handles_repository_failures() -> None:
    st = FakeStreamlit((date(2016, 2, 1), date(2016, 2, 2)))
    repository = RecordingRepository(error=RuntimeError("Query failed"))

    run_app(st, repository)

    assert repository.calls == [(date(2016, 2, 1), date(2016, 2, 2))]
    assert ("error", "Query failed") in st.messages
    assert st.bar_charts == []
