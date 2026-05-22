"""Validate the tweet A/B test schedule and results files."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


ALL_COLUMNS = {
    "tweet_number",
    "variant",
    "scheduled_at",
    "posted_at",
    "tweet_id",
    "tweet_url",
    "hook_text",
    "topic",
    "content_type",
    "is_thread",
    "has_image",
    "likes",
    "replies",
    "reposts",
    "bookmarks",
    "status",
}
SCHEDULE_REQUIRED_NONEMPTY = {
    "tweet_number",
    "variant",
    "scheduled_at",
    "hook_text",
    "topic",
    "content_type",
    "is_thread",
    "has_image",
    "status",
}
RESULT_REQUIRED_NONEMPTY = ALL_COLUMNS
METRIC_COLUMNS = ("likes", "replies", "reposts", "bookmarks")
BOOLEAN_COLUMNS = ("is_thread", "has_image")
METADATA_JOIN_COLUMNS = (
    "variant",
    "scheduled_at",
    "hook_text",
    "topic",
    "content_type",
    "is_thread",
    "has_image",
)
VALID_VARIANTS = {"A", "B"}
VALID_STATUSES = {"scheduled", "posted", "sample", "draft"}
EXPECTED_TWEETS = 34
EXPECTED_PER_VARIANT = 17
EXPECTED_POSTING_TIME = "09:00:00"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise ValueError(f"Missing required file: {path}")

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"{path} is empty or missing a header row")
        return reader.fieldnames, list(reader)


def require_columns(path: Path, fieldnames: list[str], required: set[str]) -> None:
    missing = required - set(fieldnames)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")


def require_nonempty(row: dict[str, str], columns: set[str], path: Path, row_number: int) -> None:
    for column in columns:
        if row.get(column) is None or row.get(column, "").strip() == "":
            raise ValueError(f"{path} row {row_number}: {column} is required")


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


def validate_datetime(value: str, column: str, path: Path, row_number: int) -> None:
    if not value:
        return
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{path} row {row_number}: {column} must be ISO-8601 datetime"
        ) from exc


def parse_datetime(value: str, column: str, path: Path, row_number: int) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{path} row {row_number}: {column} must be ISO-8601 datetime"
        ) from exc


def validate_url(value: str, path: Path, row_number: int) -> None:
    if not value:
        return
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{path} row {row_number}: tweet_url must be a valid URL")


def validate_boolean(value: str, column: str, path: Path, row_number: int) -> str:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"{path} row {row_number}: {column} must be true or false")
    return normalized


def validate_common_fields(
    row: dict[str, str],
    path: Path,
    row_number: int,
    required_nonempty: set[str],
) -> tuple[int, str]:
    require_nonempty(row, required_nonempty, path, row_number)
    tweet_number = parse_tweet_number(row.get("tweet_number", ""), path, row_number)
    variant = row.get("variant", "").strip()
    status = row.get("status", "").strip()

    if variant not in VALID_VARIANTS:
        raise ValueError(f"{path} row {row_number}: variant must be A or B")
    if status and status not in VALID_STATUSES:
        raise ValueError(
            f"{path} row {row_number}: status must be one of {sorted(VALID_STATUSES)}"
        )

    validate_datetime(row.get("scheduled_at", "").strip(), "scheduled_at", path, row_number)
    validate_datetime(row.get("posted_at", "").strip(), "posted_at", path, row_number)
    validate_url(row.get("tweet_url", "").strip(), path, row_number)
    for column in BOOLEAN_COLUMNS:
        validate_boolean(row.get(column, ""), column, path, row_number)

    return tweet_number, variant


def validate_schedule(schedule_path: Path) -> dict[int, dict[str, str]]:
    fieldnames, rows = read_csv(schedule_path)
    require_columns(schedule_path, fieldnames, ALL_COLUMNS)

    if len(rows) != EXPECTED_TWEETS:
        raise ValueError(
            f"{schedule_path}: expected {EXPECTED_TWEETS} rows, found {len(rows)}"
        )

    schedule: dict[int, dict[str, str]] = {}
    variant_counts: Counter[str] = Counter()
    scheduled_datetimes: list[datetime] = []
    weekday_variant_counts: dict[int, Counter[str]] = {}
    topic_variant_counts: dict[str, Counter[str]] = {}
    image_variant_counts: dict[str, Counter[str]] = {}

    for row_number, row in enumerate(rows, start=2):
        tweet_number, variant = validate_common_fields(
            row,
            schedule_path,
            row_number,
            SCHEDULE_REQUIRED_NONEMPTY,
        )
        if tweet_number in schedule:
            raise ValueError(
                f"{schedule_path} row {row_number}: duplicate tweet_number {tweet_number}"
            )

        schedule[tweet_number] = row
        variant_counts[variant] += 1
        scheduled_at = parse_datetime(
            row.get("scheduled_at", "").strip(),
            "scheduled_at",
            schedule_path,
            row_number,
        )
        scheduled_datetimes.append(scheduled_at)
        weekday_variant_counts.setdefault(scheduled_at.weekday(), Counter())[variant] += 1
        topic_variant_counts.setdefault(row["topic"].strip(), Counter())[variant] += 1
        image_variant_counts.setdefault(row["has_image"].strip().lower(), Counter())[variant] += 1

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

    sorted_datetimes = sorted(scheduled_datetimes)
    if len({dt.date() for dt in sorted_datetimes}) != EXPECTED_TWEETS:
        raise ValueError(f"{schedule_path}: schedule must have one tweet per day")

    if {dt.time().isoformat() for dt in sorted_datetimes} != {EXPECTED_POSTING_TIME}:
        raise ValueError(
            f"{schedule_path}: all scheduled_at times must be {EXPECTED_POSTING_TIME}"
        )

    for previous, current in zip(sorted_datetimes, sorted_datetimes[1:]):
        if (current.date() - previous.date()).days != 1:
            raise ValueError(
                f"{schedule_path}: scheduled_at dates must be consecutive days"
            )

    for weekday, counts in weekday_variant_counts.items():
        if abs(counts["A"] - counts["B"]) > 1:
            raise ValueError(
                f"{schedule_path}: weekday {weekday} is imbalanced "
                f"({dict(counts)})"
            )

    for topic, counts in topic_variant_counts.items():
        if counts["A"] != counts["B"]:
            raise ValueError(
                f"{schedule_path}: topic {topic} must have equal A/B rows"
            )

    for has_image, counts in image_variant_counts.items():
        if counts["A"] != counts["B"]:
            raise ValueError(
                f"{schedule_path}: has_image={has_image} must have equal A/B rows"
            )

    return schedule


def validate_results(results_path: Path, schedule: dict[int, dict[str, str]]) -> None:
    fieldnames, rows = read_csv(results_path)
    require_columns(results_path, fieldnames, ALL_COLUMNS)

    if not rows:
        raise ValueError(f"{results_path}: expected at least one result row")

    seen_tweet_numbers: set[int] = set()
    variant_counts: Counter[str] = Counter()

    for row_number, row in enumerate(rows, start=2):
        tweet_number, variant = validate_common_fields(
            row,
            results_path,
            row_number,
            RESULT_REQUIRED_NONEMPTY,
        )
        if tweet_number in seen_tweet_numbers:
            raise ValueError(
                f"{results_path} row {row_number}: duplicate tweet_number {tweet_number}"
            )
        if tweet_number not in schedule:
            raise ValueError(
                f"{results_path} row {row_number}: tweet_number {tweet_number} "
                "is not in tweet_schedule.csv"
            )

        scheduled_row = schedule[tweet_number]
        for column in METADATA_JOIN_COLUMNS:
            if row.get(column, "").strip() != scheduled_row.get(column, "").strip():
                raise ValueError(
                    f"{results_path} row {row_number}: {column} does not match "
                    "tweet_schedule.csv"
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
