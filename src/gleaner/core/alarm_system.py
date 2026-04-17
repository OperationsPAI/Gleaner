"""
Detector-span based Alarm System for Gleaner V2

We drop metrics-driven anomaly detection and treat the set of "detector spans"
(loaded from conclusion.parquet) as anomalous root-span types. This module
exposes helpers to load these spans and, for convenience, to read injection
time from env.json for warmup/processing split.
"""

import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set

import polars as pl
from rcabench_platform.v2.logging import logger

from src.gleaner.components.dataloader import load_json


def load_inject_time(input_folder: Path) -> datetime.datetime:
    """Load the injection timestamp (UTC) from env.json.

    We pick ABNORMAL_START as the injection moment (boundary between normal and
    abnormal).
    """
    env = load_json(path=input_folder / "env.json")

    normal_start = int(env["NORMAL_START"])  # kept for validation
    normal_end = int(env["NORMAL_END"])  # kept for validation
    abnormal_start = int(env["ABNORMAL_START"])
    abnormal_end = int(env["ABNORMAL_END"])  # kept for validation

    assert normal_start < normal_end <= abnormal_start < abnormal_end

    inject_time = abnormal_start
    dt = datetime.datetime.fromtimestamp(inject_time, tz=datetime.timezone.utc)
    logger.debug(f"inject_time=`{dt}` ({inject_time})")
    return dt


def try_load_inject_time(input_folder: Optional[Path]) -> Optional[float]:
    """Try to load injection time, return epoch seconds or None if failed."""
    if input_folder is None:
        return None
    try:
        return load_inject_time(input_folder).timestamp()
    except Exception as e:  # best-effort helper
        logger.warning(f"Failed to load inject time from {input_folder}: {e}")
        return None


@dataclass
class AlarmState:
    """Current alarm state consisting of detector root span names."""

    detector_root_spans: Set[str]


class AlarmSystem:
    """Alarm system powered by detector spans (no metrics).

    Attributes:
        input_folder: Dataset folder containing conclusion.parquet
        detector_weight: Weight multiplier for detector classes (e.g., 3x)
        max_detector_budget_ratio: Max share of batch budget for detector classes
            (e.g., 0.5 == 50%)
    """

    def __init__(
        self,
        input_folder: Optional[Path] = None,
        *,
        detector_weight: float = 3.0,
        max_detector_budget_ratio: float = 0.5,
    ) -> None:
        self.input_folder = input_folder
        self.detector_weight = detector_weight
        self.max_detector_budget_ratio = max_detector_budget_ratio
        self._state: Optional[AlarmState] = None

        # For compatibility with existing code paths
        self.injection_time: Optional[float] = None
        self._injection_time_loaded = False
        self._warmup_end_time: Optional[float] = None

    def set_warmup_end_time(self, warmup_end_time: float) -> None:
        self._warmup_end_time = warmup_end_time

    def load_injection_time_if_needed(self, input_folder: Optional[Path]) -> None:
        if not self._injection_time_loaded and input_folder is not None:
            ts = try_load_inject_time(input_folder)
            self.injection_time = ts
            self._injection_time_loaded = True

    def load_detector_spans(self) -> Set[str]:
        """Load detector spans (root span names) from conclusion.parquet.

        We keep rows where Issues is not null or empty. The SpanName column is
        used as the root span type identifier.
        """
        if self.input_folder is None:
            logger.info("No input_folder set for AlarmSystem; detector set is empty.")
            self._state = AlarmState(detector_root_spans=set())
            return self._state.detector_root_spans

        path = self.input_folder / "conclusion.parquet"
        if not path.exists():
            logger.info(
                f"No conclusion.parquet found at {path}; detector set is empty."
            )
            self._state = AlarmState(detector_root_spans=set())
            return self._state.detector_root_spans

        df = pl.read_parquet(path)
        if (
            df.is_empty()
            or ("SpanName" not in df.columns)
            or ("Issues" not in df.columns)
        ):
            logger.info("Empty or invalid conclusion.parquet; detector set is empty.")
            self._state = AlarmState(detector_root_spans=set())
            return self._state.detector_root_spans

        filtered = df.filter(
            (pl.col("Issues").is_not_null())
            & (pl.col("Issues") != "{}")
            & (pl.col("Issues") != "")
        )

        if filtered.is_empty():
            logger.info(
                "No detector issues found in conclusion.parquet (normal for normal-only datasets)"
            )
            spans = set()
        else:
            spans = set(filtered.get_column("SpanName").unique().to_list())
            logger.info(f"Loaded {len(spans)} detector root span types.")

        self._state = AlarmState(detector_root_spans=spans)
        return spans

    def get_detector_spans_cached(self) -> Set[str]:
        """Get cached detector spans if available, else load them."""
        if self._state is None:
            return self.load_detector_spans()
        return self._state.detector_root_spans
