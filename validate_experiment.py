"""Validate the tweet A/B test schedule and results files."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


REQUIRED_RESULT_COLUMNS = {
    "tweet_number",
    "variant",
    "likes",
    "replies",
    "reposts",
    "bookmarks",
}
METRIC_COLUMNS = ("likes", "replies", "reposts", "bookmarks")
VALID_VARIANTS = {"A", "B"}
EXPECTED_TWEETS = 34
EXPECTED_PER_VARIANT = 17


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise ValueError(f"Missing required file: {path}")

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"{path} is empty or missing a header row")
        return list(reader)


def parse_tweet_number(value: str, path: Path, row_number: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{path} row {row_number}: tweet_number must be an integer"
        ) from exc

    if parsed <= 0:
        raise ValueError(f"{path} row {row_number}: tweet_number must be positive")
    return parsed


def validate_metric(value: str, column: str, path: Path, row_number: int) -> None:
    if value is None or str(value).strip() == "":
        raise ValueError(f"{path} row {row_number}: {column} is required")

    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{path} row {row_number}: {column} must be numeric") from exc

    if parsed < 0:
        raise ValueError(f"{path} row {row_number}: {column} must be non-negative")

    if not parsed.is_integer():
        raise ValueError(f"{path} row {row_number}: {column} must be integer-like")


def validate_schedule(schedule_path: Path) -> dict[int, str]:
    rows = read_csv(schedule_path)
    if len(rows) != EXPECTED_TWEETS:
        raise ValueError(
            f"{schedule_path}: expected {EXPECTED_TWEETS} rows, found {len(rows)}"
        )

    required_columns = {"tweet_number", "variant"}
    missing_columns = required_columns - set(rows[0].keys())
    if missing_columns:
        raise ValueError(
            f"{schedule_path}: missing columns {sorted(missing_columns)}"
        )

    schedule: dict[int, str] = {}
    variant_counts: Counter[str] = Counter()

    for row_number, row in enumerate(rows, start=2):
        tweet_number = parse_tweet_number(row.get("tweet_number", ""), schedule_path, row_number)
        variant = row.get("variant", "").strip()

        if variant not in VALID_VARIANTS:
            raise ValueError(
                f"{schedule_path} row {row_number}: variant must be A or B"
            )
        if tweet_number in schedule:
            raise ValueError(
                f"{schedule_path} row {row_number}: duplicate tweet_number {tweet_number}"
            )

        schedule[tweet_number] = variant
        variant_counts[variant] += 1

    for variant in sorted(VALID_VARIANTS):
        if variant_counts[variant] != EXPECTED_PER_VARIANT:
            raise ValueError(
                f"{schedule_path}: expected {EXPECTED_PER_VARIANT} {variant} rows, "
                f"found {variant_counts[variant]}"
            )

    expected_numbers = set(range(1, EXPECTED_TWEETS + 1))
    if set(schedule) != expected_numbers:
        raise ValueError(
            f"{schedule_path}: tweet_number must cover 1..{EXPECTED_TWEETS}"
        )

    return schedule


def validate_results(results_path: Path, schedule: dict[int, str]) -> None:
    rows = read_csv(results_path)
    if not rows:
        raise ValueError(f"{results_path}: expected at least one result row")

    missing_columns = REQUIRED_RESULT_COLUMNS - set(rows[0].keys())
    if missing_columns:
        raise ValueError(f"{results_path}: missing columns {sorted(missing_columns)}")

    seen_tweet_numbers: set[int] = set()
    variant_counts: Counter[str] = Counter()

    for row_number, row in enumerate(rows, start=2):
        tweet_number = parse_tweet_number(row.get("tweet_number", ""), results_path, row_number)
        variant = row.get("variant", "").strip()

        if tweet_number in seen_tweet_numbers:
            raise ValueError(
                f"{results_path} row {row_number}: duplicate tweet_number {tweet_number}"
            )
        if tweet_number not in schedule:
            raise ValueError(
                f"{results_path} row {row_number}: tweet_number {tweet_number} "
                "is not in tweet_schedule.csv"
            )
        if variant not in VALID_VARIANTS:
            raise ValueError(
                f"{results_path} row {row_number}: variant must be A or B"
            )
        if variant != schedule[tweet_number]:
            raise ValueError(
                f"{results_path} row {row_number}: variant {variant} does not match "
                f"scheduled variant {schedule[tweet_number]}"
            )

        for column in METRIC_COLUMNS:
            validate_metric(row.get(column, ""), column, results_path, row_number)

        seen_tweet_numbers.add(tweet_number)
        variant_counts[variant] += 1

    missing_results = sorted(set(schedule) - seen_tweet_numbers)
    if missing_results:
        print(
            "Warning: results are incomplete for scheduled tweet_numbers "
            f"{missing_results}",
            file=sys.stderr,
        )

    print(
        "Validation passed: "
        f"{len(schedule)} scheduled tweets, {len(rows)} result rows, "
        f"results by variant {dict(sorted(variant_counts.items()))}."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schedule", default="tweet_schedule.csv", type=Path)
    parser.add_argument("--results", default="data/experiment_results.csv", type=Path)
    args = parser.parse_args()

    try:
        schedule = validate_schedule(args.schedule)
        validate_results(args.results, schedule)
    except ValueError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
