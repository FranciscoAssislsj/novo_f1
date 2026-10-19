import os
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd

from novo_f1.storage.parquet_store import (
    ParquetStore,
    coerce_mixed_columns,
    partition_name,
)


def test_partition_name():
    assert partition_name(session_key=1, driver=2) == "session_key=1_driver=2"


def test_path_layout(tmp_path):
    store = ParquetStore(tmp_path)

    path = store.path_for("laps", 2024, "session_key=9161")

    assert path == tmp_path / "raw" / "laps" / "year=2024" / "session_key=9161.parquet"


def test_save_and_load_roundtrip_with_lists(tmp_path, laps):
    store = ParquetStore(tmp_path)
    path = store.path_for("laps", 2023, "session_key=9161")

    store.save(laps, path)
    loaded = store.load(path)

    assert store.exists(path)
    assert len(loaded) == len(laps)
    assert list(loaded["segments_sector_1"].iloc[0]) == [2048, 2049]


def test_save_handles_mixed_gap_types(tmp_path, intervals):
    store = ParquetStore(tmp_path)
    path = store.path_for("intervals", 2023, "x")

    store.save(intervals, path)
    loaded = store.load(path)

    assert loaded["gap_to_leader"].tolist()[1:] == ["1.234", "+1 LAP"]
    assert pd.isna(loaded["gap_to_leader"].iloc[0])


def test_coerce_mixed_columns_serialises_mixed_lists():
    frame = pd.DataFrame({"duration": pd.Series([[1.0, None], 90.5, None, np.nan])})

    result = coerce_mixed_columns(frame)

    assert result["duration"].tolist()[:2] == ["[1.0, null]", "90.5"]
    assert result["duration"].iloc[2:].isna().all()


def test_coerce_keeps_consistent_columns():
    frame = pd.DataFrame({"a": [1, 2], "b": [[1], [2]]})

    result = coerce_mixed_columns(frame)

    assert result["b"].tolist() == [[1], [2]]


def test_is_expired(tmp_path):
    store = ParquetStore(tmp_path)
    path = store.path_for("meetings", 2026, "all")
    store.save(pd.DataFrame({"a": [1]}), path)
    old = datetime(2026, 1, 1, tzinfo=UTC).timestamp()
    os.utime(path, (old, old))

    assert store.is_expired(path, timedelta(hours=24), datetime(2026, 1, 3, tzinfo=UTC))
    assert not store.is_expired(
        path, timedelta(hours=24), datetime(2026, 1, 1, 12, tzinfo=UTC)
    )
    assert store.is_expired(tmp_path / "missing.parquet", timedelta(hours=1))
