#!/usr/bin/env python3
"""Compare expected artifact outputs against a freshly generated actual directory."""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

DEFAULT_FILES = (
    "rq4_efficiency_results.md",
    "rq4_efficiency_summary.csv",
    "rq4_efficiency_summary.json",
)
DEFAULT_IGNORED_JSON_PATHS = ("config.output_dir",)
OUTPUT_DIR_LINE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:output\s+directory|output_dir)\s*[:=].*$",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare reduced artifact expected outputs against actual outputs."
    )
    parser.add_argument("--expected", required=True, type=Path, help="Expected output directory")
    parser.add_argument("--actual", required=True, type=Path, help="Actual output directory")
    parser.add_argument(
        "--file",
        action="append",
        dest="files",
        help="Relative file to compare. Defaults to the three RQ4 output files.",
    )
    parser.add_argument(
        "--abs-tol",
        type=float,
        default=1e-12,
        help="Absolute tolerance for numeric JSON/CSV values (default: 1e-12)",
    )
    parser.add_argument(
        "--rel-tol",
        type=float,
        default=1e-12,
        help="Relative tolerance for numeric JSON/CSV values (default: 1e-12)",
    )
    parser.add_argument(
        "--ignore-json-path",
        action="append",
        default=list(DEFAULT_IGNORED_JSON_PATHS),
        help=(
            "Dot-separated JSON path to ignore; repeatable. "
            "Defaults to config.output_dir."
        ),
    )
    parser.add_argument(
        "--ignore-markdown-output-dir",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Normalize markdown output directory/output_dir lines (default: enabled)",
    )
    return parser.parse_args()


def rel_files(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}


def numeric_equal(expected: float, actual: float, abs_tol: float, rel_tol: float) -> bool:
    if math.isnan(expected) or math.isnan(actual):
        return math.isnan(expected) and math.isnan(actual)
    if math.isinf(expected) or math.isinf(actual):
        return expected == actual
    return abs(expected - actual) <= max(abs_tol, rel_tol * max(abs(expected), abs(actual)))


def json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int | float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def as_number(value: str) -> float | None:
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) or value.lower() in {"inf", "+inf", "-inf", "nan"} else number


def compare_json(
    expected: Any,
    actual: Any,
    path: str,
    ignored_paths: set[str],
    abs_tol: float,
    rel_tol: float,
    errors: list[str],
) -> None:
    if path in ignored_paths:
        return
    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = set(expected)
        actual_keys = set(actual)
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        if missing:
            errors.append(f"JSON key mismatch at {path or '<root>'}: missing keys {missing}")
        if extra:
            errors.append(f"JSON key mismatch at {path or '<root>'}: extra keys {extra}")
        for key in sorted(expected_keys & actual_keys):
            child_path = f"{path}.{key}" if path else key
            compare_json(expected[key], actual[key], child_path, ignored_paths, abs_tol, rel_tol, errors)
        return
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            errors.append(
                f"JSON length mismatch at {path or '<root>'}: expected {len(expected)}, got {len(actual)}"
            )
            return
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual, strict=True)):
            compare_json(
                expected_item,
                actual_item,
                f"{path}[{index}]",
                ignored_paths,
                abs_tol,
                rel_tol,
                errors,
            )
        return
    if isinstance(expected, bool) or isinstance(actual, bool):
        if not isinstance(expected, bool) or not isinstance(actual, bool):
            errors.append(
                f"JSON type mismatch at {path}: expected {json_type_name(expected)} "
                f"{expected!r}, got {json_type_name(actual)} {actual!r}"
            )
        elif expected != actual:
            errors.append(f"JSON value mismatch at {path}: expected {expected!r}, got {actual!r}")
        return
    if isinstance(expected, int | float) and isinstance(actual, int | float):
        expected_number = float(expected)
        actual_number = float(actual)
        if not numeric_equal(expected_number, actual_number, abs_tol, rel_tol):
            errors.append(
                f"JSON numeric mismatch at {path}: expected {expected!r}, got {actual!r} "
                f"(abs_tol={abs_tol}, rel_tol={rel_tol})"
            )
        return
    if expected != actual:
        errors.append(f"JSON value mismatch at {path}: expected {expected!r}, got {actual!r}")


def compare_json_file(
    expected_path: Path,
    actual_path: Path,
    ignored_paths: set[str],
    abs_tol: float,
    rel_tol: float,
) -> list[str]:
    errors: list[str] = []
    with expected_path.open(encoding="utf-8") as handle:
        expected = json.load(handle)
    with actual_path.open(encoding="utf-8") as handle:
        actual = json.load(handle)
    compare_json(expected, actual, "", ignored_paths, abs_tol, rel_tol, errors)
    return errors


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def row_key(row: dict[str, str], headers: list[str], index: int) -> str:
    if headers:
        return row.get(headers[0], f"#{index}")
    return f"#{index}"


def compare_csv_file(expected_path: Path, actual_path: Path, abs_tol: float, rel_tol: float) -> list[str]:
    errors: list[str] = []
    expected_headers, expected_rows = read_csv(expected_path)
    actual_headers, actual_rows = read_csv(actual_path)
    if expected_headers != actual_headers:
        errors.append(f"CSV header mismatch: expected {expected_headers}, got {actual_headers}")
        return errors
    expected_map = {
        row_key(row, expected_headers, index): row for index, row in enumerate(expected_rows)
    }
    actual_map = {row_key(row, actual_headers, index): row for index, row in enumerate(actual_rows)}
    if len(expected_map) != len(expected_rows) or len(actual_map) != len(actual_rows):
        errors.append("CSV duplicate row keys; falling back requires unique first-column values")
        return errors
    missing = sorted(set(expected_map) - set(actual_map))
    extra = sorted(set(actual_map) - set(expected_map))
    if missing:
        errors.append(f"CSV missing rows by {expected_headers[0] if expected_headers else 'row'}: {missing}")
    if extra:
        errors.append(f"CSV extra rows by {actual_headers[0] if actual_headers else 'row'}: {extra}")
    for key in sorted(set(expected_map) & set(actual_map)):
        for header in expected_headers:
            expected_value = expected_map[key][header]
            actual_value = actual_map[key][header]
            expected_number = as_number(expected_value)
            actual_number = as_number(actual_value)
            if expected_number is not None and actual_number is not None:
                if not numeric_equal(expected_number, actual_number, abs_tol, rel_tol):
                    errors.append(
                        f"CSV numeric mismatch at row {key!r}, column {header!r}: "
                        f"expected {expected_value!r}, got {actual_value!r} "
                        f"(abs_tol={abs_tol}, rel_tol={rel_tol})"
                    )
            elif expected_value != actual_value:
                errors.append(
                    f"CSV value mismatch at row {key!r}, column {header!r}: "
                    f"expected {expected_value!r}, got {actual_value!r}"
                )
    return errors


def normalized_markdown_lines(path: Path, ignore_output_dir: bool) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not ignore_output_dir:
        return lines
    return [
        "<normalized output_dir>" if OUTPUT_DIR_LINE_RE.match(line) else line
        for line in lines
    ]


def compare_markdown_file(expected_path: Path, actual_path: Path, ignore_output_dir: bool) -> list[str]:
    expected_lines = normalized_markdown_lines(expected_path, ignore_output_dir)
    actual_lines = normalized_markdown_lines(actual_path, ignore_output_dir)
    if expected_lines == actual_lines:
        return []
    diff = difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile=str(expected_path),
        tofile=str(actual_path),
        lineterm="",
        n=3,
    )
    diff_lines = list(diff)
    max_lines = 80
    summary = "\n".join(diff_lines[:max_lines])
    if len(diff_lines) > max_lines:
        summary += f"\n... diff truncated after {max_lines} lines"
    return ["Markdown text mismatch:\n" + summary]


def compare_file(args: argparse.Namespace, relative_file: str) -> list[str]:
    expected_path = args.expected / relative_file
    actual_path = args.actual / relative_file
    errors: list[str] = []
    if not expected_path.exists():
        errors.append(f"Missing expected file: {expected_path}")
    if not actual_path.exists():
        errors.append(f"Missing actual file: {actual_path}")
    if errors:
        return errors
    suffix = expected_path.suffix.lower()
    if suffix == ".json":
        return compare_json_file(
            expected_path,
            actual_path,
            set(args.ignore_json_path or []),
            args.abs_tol,
            args.rel_tol,
        )
    if suffix == ".csv":
        return compare_csv_file(expected_path, actual_path, args.abs_tol, args.rel_tol)
    if suffix in {".md", ".markdown"}:
        return compare_markdown_file(
            expected_path, actual_path, args.ignore_markdown_output_dir
        )
    if expected_path.read_bytes() != actual_path.read_bytes():
        return [f"Binary/text file mismatch: {relative_file}"]
    return []


def main() -> int:
    args = parse_args()
    files = args.files or list(DEFAULT_FILES)
    errors: list[str] = []
    if not args.expected.is_dir():
        errors.append(f"Expected directory does not exist: {args.expected}")
    if not args.actual.is_dir():
        errors.append(f"Actual directory does not exist: {args.actual}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2

    selected = set(files)
    expected_extra = sorted(rel_files(args.expected) - selected)
    actual_extra = sorted(rel_files(args.actual) - selected)
    if expected_extra:
        errors.append(f"Extra expected files not compared: {expected_extra}")
    if actual_extra:
        errors.append(f"Extra actual files not compared: {actual_extra}")

    for relative_file in files:
        file_errors = compare_file(args, relative_file)
        errors.extend(f"{relative_file}: {error}" for error in file_errors)

    if errors:
        print("Expected-output comparison failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Expected-output comparison passed for {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
