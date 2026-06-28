#!/usr/bin/env python3
"""Run TracePicker in its isolated env and write platform-compatible outputs."""

from __future__ import annotations

import dataclasses
import time
import traceback
from pathlib import Path
import sys

TRACEPICKER_SRC = Path(__file__).resolve().parents[2] / "third_party" / "TracePicker" / "src"
if str(TRACEPICKER_SRC) not in sys.path:
    sys.path.insert(0, str(TRACEPICKER_SRC))

import polars as pl
import typer
from loguru import logger as loguru_logger

loguru_logger.remove()
loguru_logger.add(sys.stderr, level="ERROR")

from rcabench_platform.v2.config import get_config
from rcabench_platform.v2.datasets.spec import get_datapack_folder, get_datapack_list
from rcabench_platform.v2.samplers.experiments.single import calculate_sampler_performance, _save_sampled_traces
from rcabench_platform.v2.samplers.spec import SamplingMode, SampleResult
from rcabench_platform.v2.utils.serde import save_parquet
from tqdm import tqdm
from tracepicker.algorithms.platform_adapter import run_tracepicker

app = typer.Typer(pretty_exceptions_show_locals=False)


def _rate_label(rate: float) -> str:
    return f"{rate:.3f}".rstrip("0").rstrip(".")


def _output_folder(dataset: str, datapack: str, rate: float, mode: str) -> Path:
    return get_datapack_folder(dataset, datapack) / "sampled" / f"tracepicker_{_rate_label(rate)}_{mode}"


@app.command()
def batch(
    datasets: list[str] = typer.Option(..., "-d", "--dataset"),
    sampling_rates: list[float] = typer.Option(..., "-r", "--rate"),
    modes: list[str] = typer.Option(["offline"], "-m", "--mode"),
    sample_datapacks: int | None = typer.Option(None, "--sample-datapacks"),
    clear: bool = typer.Option(False, "--clear"),
    skip_finished: bool = typer.Option(True, "--skip-finished/--no-skip-finished"),
    seed: int = typer.Option(42, "--seed"),
):
    tasks: list[tuple[str, str, float, str]] = []
    for dataset in datasets:
        datapacks = get_datapack_list(dataset)
        if sample_datapacks is not None:
            datapacks = datapacks[:sample_datapacks]
        for datapack in datapacks:
            for rate in sampling_rates:
                for mode in modes:
                    tasks.append((dataset, datapack, rate, mode))

    for dataset, datapack, rate, mode in tqdm(tasks, desc="TracePicker full sampling"):
        run_one(dataset, datapack, rate, SamplingMode(mode), clear=clear, skip_finished=skip_finished, seed=seed)


@app.command("perf-report")
def perf_report(
    datasets: list[str] = typer.Option(..., "-d", "--dataset"),
    sampling_rates: list[float] | None = typer.Option(None, "-r", "--rate"),
    modes: list[str] | None = typer.Option(None, "-m", "--mode"),
):
    rows = []
    for dataset in datasets:
        for datapack in get_datapack_list(dataset):
            sampled = get_datapack_folder(dataset, datapack) / "sampled"
            if not sampled.exists():
                continue
            for folder in sampled.glob("tracepicker_*"):
                perf = folder / "perf.parquet"
                if not perf.exists():
                    continue
                parts = folder.name.split("_")
                rate = float(parts[-2])
                mode = parts[-1]
                if sampling_rates is not None and rate not in sampling_rates:
                    continue
                if modes is not None and mode not in modes:
                    continue
                df = pl.read_parquet(perf).with_columns(
                    pl.lit(dataset).alias("dataset"),
                    pl.lit(datapack).alias("datapack"),
                    pl.lit("tracepicker").alias("sampler"),
                    pl.lit(rate).alias("sampling_rate"),
                    pl.lit(mode).alias("mode"),
                )
                rows.append(df)
    if not rows:
        raise typer.Exit("no TracePicker perf.parquet files found")
    detailed = pl.concat(rows, how="vertical_relaxed", rechunk=True)
    for dataset in datasets:
        out = get_config().output / "sampler_reports" / dataset
        out.mkdir(parents=True, exist_ok=True)
        ds = detailed.filter(pl.col("dataset") == dataset)
        if len(ds) == 0:
            continue
        save_parquet(ds, path=out / "tracepicker.detailed_perf.parquet")
        agg = ds.group_by(["sampler", "dataset", "sampling_rate", "mode"]).agg(
            pl.len().alias("datapack_count"),
            pl.col("sampled_count").mean().alias("avg_sampled_count"),
            pl.col("total_traces").mean().alias("avg_total_traces"),
            pl.col("actual_sampling_rate").mean().alias("avg_actual_sampling_rate"),
            pl.col("comprehensiveness").mean().alias("avg_api_coverage"),
            pl.col("path_coverage").mean().alias("avg_path_coverage"),
            pl.col("path_coverage_dedup").mean().alias("avg_path_coverage_dedup"),
            pl.col("unique_trace_coverage").mean().alias("avg_unique_trace_coverage"),
            pl.col("shannon_entropy").mean().alias("avg_shannon_entropy"),
            pl.col("benefit_cost_ratio").mean().alias("avg_benefit_cost_ratio"),
            pl.col("runtime_per_trace_ms").mean().alias("avg_runtime_per_trace_ms"),
        )
        save_parquet(agg, path=out / "tracepicker.aggregated_perf.parquet")
        merge_report(out / "detailed_perf.parquet", ds, key_cols=["dataset", "datapack", "sampler", "sampling_rate", "mode"])
        merge_report(out / "aggregated_perf.parquet", agg, key_cols=["dataset", "sampler", "sampling_rate", "mode"])


def merge_report(path: Path, tracepicker_df: pl.DataFrame, *, key_cols: list[str]) -> None:
    if path.exists():
        base = pl.read_parquet(path)
        if "sampler" in base.columns:
            base = base.filter(pl.col("sampler") != "tracepicker")
        combined = pl.concat([base, tracepicker_df], how="diagonal_relaxed", rechunk=True)
    else:
        combined = tracepicker_df
    save_parquet(combined, path=path)


def run_one(dataset: str, datapack: str, rate: float, mode: SamplingMode, *, clear: bool, skip_finished: bool, seed: int) -> None:
    input_folder = get_datapack_folder(dataset, datapack)
    output_folder = _output_folder(dataset, datapack, rate, mode.value)
    finished = output_folder / ".finished"
    if clear and output_folder.exists():
        import shutil
        shutil.rmtree(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    if skip_finished and finished.exists():
        return
    try:
        t0 = time.time()
        result = run_tracepicker(data_folder=input_folder, sample_rate=rate, seed=seed)
        runtime = time.time() - t0
        exc = None
    except Exception as e:  # keep platform-style failure materialized
        traceback.print_exc()
        result = {"sampled_trace_ids": []}
        runtime = None
        exc = e

    sampled_ids = set(result.get("sampled_trace_ids", []))
    rows = []
    for trace_id in sampled_ids:
        rows.append(dataclasses.asdict(SampleResult(trace_id=str(trace_id), sample_score=1.0)))
    sampled_df = pl.DataFrame(rows, schema={"trace_id": pl.String, "sample_score": pl.Float64})
    perf = calculate_sampler_performance(input_folder, sampled_df, rate, mode, runtime, dataset)
    output_df = sampled_df.with_columns(
        pl.lit("tracepicker").alias("sampler"),
        pl.lit(dataset).alias("dataset"),
        pl.lit(datapack).alias("datapack"),
        pl.lit(rate).alias("sampling_rate"),
        pl.lit(mode.value).alias("mode"),
        pl.lit(runtime, dtype=pl.Float64).alias("runtime.seconds"),
        pl.lit(type(exc).__name__ if exc else None, dtype=pl.String).alias("exception.type"),
    )
    save_parquet(output_df, path=output_folder / f"{mode.value}.parquet")
    save_parquet(pl.DataFrame([perf]), path=output_folder / "perf.parquet")
    _save_sampled_traces(input_folder, output_folder, sampled_df)
    finished.touch()


if __name__ == "__main__":
    app()
