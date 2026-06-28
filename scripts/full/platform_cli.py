#!/usr/bin/env python3
"""Offline-only RCAbench Platform CLI for the full artifact path.

The upstream platform CLI imports online/container modules that depend on a
separate rcabench OpenAPI package. Full reproduction only needs offline sample
and eval commands, so this wrapper registers the paper algorithms and exposes
only those Typer subcommands.
"""

from __future__ import annotations

import multiprocessing
import os
import sys
from pathlib import Path

import typer
from tqdm.auto import tqdm

ROOT = Path(__file__).resolve().parents[2]
for path in [
    ROOT,
    ROOT / "third_party" / "TraStrainer" / "src",
    ROOT / "third_party" / "ShapleyIQ" / "src",
    ROOT / "third_party" / "Nezha" / "src",
]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rcabench_platform.v2.algorithms.spec import global_algorithm_registry
from rcabench_platform.v2.cli import eval as eval_cli
from rcabench_platform.v2.cli import sample as sample_cli
from rcabench_platform.v2.logging import logger
from rcabench_platform.v2.samplers.random_ import RandomSampler
from rcabench_platform.v2.samplers.spec import global_sampler_registry
from rcabench_platform.v2.utils.env import getenv_bool

from gleaner import (
    AnomalyPureDiversityVariant,
    GleanerSampler,
    LatencyDominateVariant,
    LogDominateVariant,
    NoAnomalyDetectionVariant,
    NoDPPVariant,
    NoLogsNoADVariant,
    NoLogsVariant,
    NoRebalanceVariant,
    PureDiversityVariant,
    TopScoreVariant,
    WLKernelVariant,
)

app = typer.Typer(pretty_exceptions_show_locals=False)


def configure_logging() -> None:
    logger.remove()
    level = os.getenv("GLEANER_PLATFORM_LOG_LEVEL", os.getenv("GLEANER_LOG_LEVEL", "ERROR"))
    if os.getenv("GLEANER_DISABLE_LOGS", "0") == "1":
        return
    logger.add(
        lambda msg: tqdm.write(msg, end=""),
        level=level,
        colorize=getenv_bool("LOGURU_COLORIZE", default=True),
        enqueue=True,
        context=multiprocessing.get_context("spawn"),
    )


def register_samplers() -> None:
    registry = global_sampler_registry()
    registry.update(
        {
            "random": RandomSampler,
            "gleaner": GleanerSampler,
            "gleaner_no_logs": NoLogsVariant,
            "gleaner_no_ad": NoAnomalyDetectionVariant,
            "gleaner_no_logs_no_ad": NoLogsNoADVariant,
            "gleaner_pure_diversity": PureDiversityVariant,
            "gleaner_wl_kernel": WLKernelVariant,
            "gleaner_no_dpp": NoDPPVariant,
            "gleaner_top_score": TopScoreVariant,
            "gleaner_log_dominate": LogDominateVariant,
            "gleaner_latency_dominate": LatencyDominateVariant,
            "gleaner_no_rebalance": NoRebalanceVariant,
            "gleaner_anomaly_pure_diversity": AnomalyPureDiversityVariant,
        }
    )

    # Registers trastrainer, trastrainer_no_metrics, sifter, sieve, and wt.
    import trastrainer.register_samplers  # noqa: F401


def register_algorithms() -> None:
    from nezha.rcabench_adapter import NezhaAlgorithm
    from shapleyiq.platform.algorithms import MicroRCA, ShapleyRCA

    registry = global_algorithm_registry()
    registry.update(
        {
            "microrca": MicroRCA,
            "shapleyiq": ShapleyRCA,
            "nezha": NezhaAlgorithm,
        }
    )


@app.callback()
def _callback() -> None:
    configure_logging()


def main() -> None:
    register_samplers()
    register_algorithms()
    app.add_typer(sample_cli.app, name="sample")
    app.add_typer(eval_cli.app, name="eval")
    app()


if __name__ == "__main__":
    main()
