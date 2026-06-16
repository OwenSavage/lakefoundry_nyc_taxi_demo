from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from nyc_taxi_trip_explorer.data import (
    DataRetrievalError,
    DatabricksTaxiRepository,
    InvalidDateRangeError,
    QuerySpec,
    build_query_spec,
    normalise_trip_frame,
)


class RecordingClient:
    def __init__(self, frame: pd.DataFrame | Exception):
        self.frame = frame
        self.calls: list[str] = []

    def fetch_dataframe(self, query: str) -> pd.DataFrame:
        self.calls.append(query)
        if isinstance(self.frame, Exception):
            raise self.frame
        return self.frame.copy()


@pytest.fixture
def raw_trip_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "pickup_datetime": [
                "2016-02-01T08:15:00",
                "2016-02-01T09:45:00",
                "2016-02-02T08:20:00",
            ]
        }
    )


def test_build_query_spec_without_filters_targets_sample_table() -> None:
    spec = build_query_spec(None, None)

    assert isinstance(spec, QuerySpec)
    assert "FROM samples.nyctaxi.trips" in spec.sql
    assert "WHERE" not in spec.sql
    assert spec.start_date is None
    assert spec.end_date is None


def test_build_query_spec_with_filters_adds_bounded_date_predicate() -> None:
    spec = build_query_spec(date(2016, 2, 1), date(2016, 2, 3))

    assert "pickup_datetime >= DATE '2016-02-01'" in spec.sql
    assert "pickup_datetime < DATE '2016-02-04'" in spec.sql
    assert spec.start_date == date(2016, 2, 1)
    assert spec.end_date == date(2016, 2, 3)


def test_build_query_spec_rejects_invalid_range() -> None:
    with pytest.raises(InvalidDateRangeError):
        build_query_spec(date(2016, 2, 4), date(2016, 2, 3))


def test_normalise_trip_frame_returns_daily_and_hourly_counts(raw_trip_frame: pd.DataFrame) -> None:
    result = normalise_trip_frame(raw_trip_frame)

    assert result.trip_count == 3
    assert result.daily.to_dict("records") == [
        {"pickup_date": date(2016, 2, 1), "trip_count": 2},
        {"pickup_date": date(2016, 2, 2), "trip_count": 1},
    ]
    assert result.hourly.to_dict("records") == [
        {"pickup_hour": 8, "trip_count": 2},
        {"pickup_hour": 9, "trip_count": 1},
    ]


def test_normalise_trip_frame_handles_empty_results() -> None:
    result = normalise_trip_frame(pd.DataFrame({"pickup_datetime": []}))

    assert result.trip_count == 0
    assert result.daily.empty
    assert result.hourly.empty


def test_repository_load_trips_returns_aggregated_results(raw_trip_frame: pd.DataFrame) -> None:
    client = RecordingClient(raw_trip_frame)
    repository = DatabricksTaxiRepository(client)

    result = repository.load_trips(start_date=date(2016, 2, 1), end_date=date(2016, 2, 2))

    assert result.trip_count == 3
    assert len(client.calls) == 1
    assert "DATE '2016-02-01'" in client.calls[0]


def test_repository_wraps_runtime_failures() -> None:
    client = RecordingClient(RuntimeError("warehouse unavailable"))
    repository = DatabricksTaxiRepository(client)

    with pytest.raises(DataRetrievalError):
        repository.load_trips()
