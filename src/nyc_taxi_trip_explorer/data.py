from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Protocol

import pandas as pd

TABLE_NAME = "samples.nyctaxi.trips"


class InvalidDateRangeError(ValueError):
    """Raised when a date range is inverted."""


class DataRetrievalError(RuntimeError):
    """Raised when trip data cannot be fetched from the backend."""


class DataFrameClient(Protocol):
    def fetch_dataframe(self, query: str) -> pd.DataFrame: ...


@dataclass(frozen=True)
class QuerySpec:
    sql: str
    start_date: date | None
    end_date: date | None


@dataclass(frozen=True)
class TripAggregates:
    daily: pd.DataFrame
    hourly: pd.DataFrame
    trip_count: int


class DatabricksSqlClient:
    def __init__(self, connection) -> None:
        self._connection = connection

    def fetch_dataframe(self, query: str) -> pd.DataFrame:
        with self._connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
        return pd.DataFrame(rows, columns=columns)


class DatabricksTaxiRepository:
    def __init__(self, client: DataFrameClient) -> None:
        self._client = client

    def load_trips(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> TripAggregates:
        spec = build_query_spec(start_date, end_date)
        try:
            frame = self._client.fetch_dataframe(spec.sql)
        except Exception as exc:  # pragma: no cover - exercised via tests with broad runtime errors
            raise DataRetrievalError(str(exc)) from exc
        return normalise_trip_frame(frame)


def build_query_spec(start_date: date | None, end_date: date | None) -> QuerySpec:
    if start_date and end_date and start_date > end_date:
        raise InvalidDateRangeError("Start date must be on or before end date.")

    sql = ["SELECT pickup_datetime", f"FROM {TABLE_NAME}"]
    if start_date and end_date:
        next_day = end_date + timedelta(days=1)
        sql.append(
            "WHERE pickup_datetime >= DATE '{start}' AND pickup_datetime < DATE '{end}'".format(
                start=start_date.isoformat(),
                end=next_day.isoformat(),
            )
        )

    sql.append("ORDER BY pickup_datetime")
    return QuerySpec(sql="\n".join(sql), start_date=start_date, end_date=end_date)


def normalise_trip_frame(frame: pd.DataFrame) -> TripAggregates:
    if frame.empty:
        return TripAggregates(
            daily=pd.DataFrame(columns=["pickup_date", "trip_count"]),
            hourly=pd.DataFrame(columns=["pickup_hour", "trip_count"]),
            trip_count=0,
        )

    timestamps = pd.to_datetime(frame["pickup_datetime"], errors="coerce")
    clean_frame = pd.DataFrame({"pickup_datetime": timestamps}).dropna()

    if clean_frame.empty:
        return TripAggregates(
            daily=pd.DataFrame(columns=["pickup_date", "trip_count"]),
            hourly=pd.DataFrame(columns=["pickup_hour", "trip_count"]),
            trip_count=0,
        )

    clean_frame["pickup_date"] = clean_frame["pickup_datetime"].dt.date
    clean_frame["pickup_hour"] = clean_frame["pickup_datetime"].dt.hour

    daily = (
        clean_frame.groupby("pickup_date")
        .size()
        .reset_index(name="trip_count")
        .sort_values("pickup_date")
        .reset_index(drop=True)
    )
    hourly = (
        clean_frame.groupby("pickup_hour")
        .size()
        .reset_index(name="trip_count")
        .sort_values("pickup_hour")
        .reset_index(drop=True)
    )

    return TripAggregates(daily=daily, hourly=hourly, trip_count=int(len(clean_frame)))


def default_repository() -> DatabricksTaxiRepository:
    import os

    from databricks import sql
    from databricks.sdk.core import Config

    cfg = Config()
    warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
    if not warehouse_id:
        raise DataRetrievalError("DATABRICKS_WAREHOUSE_ID is not configured.")

    connection = sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        credentials_provider=lambda: cfg.authenticate,
    )
    return DatabricksTaxiRepository(DatabricksSqlClient(connection))
