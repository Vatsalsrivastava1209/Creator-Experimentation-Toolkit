from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from validate_experiment import validate_results, validate_schedule


ROOT = Path(__file__).resolve().parents[1]


def copy_fixture(tmp_path: Path) -> tuple[Path, Path]:
    schedule = tmp_path / "tweet_schedule.csv"
    results = tmp_path / "experiment_results.csv"
    shutil.copy(ROOT / "tweet_schedule.csv", schedule)
    shutil.copy(ROOT / "data" / "experiment_results.csv", results)
    return schedule, results


def mutate_csv(path: Path, mutator) -> None:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    mutator(rows)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_valid_sample_data_passes(tmp_path: Path) -> None:
    schedule_path, results_path = copy_fixture(tmp_path)
    schedule = validate_schedule(schedule_path)
    validate_results(results_path, schedule)


def test_missing_results_file_fails(tmp_path: Path) -> None:
    schedule_path, _ = copy_fixture(tmp_path)
    schedule = validate_schedule(schedule_path)
    with pytest.raises(ValueError, match="Missing required file"):
        validate_results(tmp_path / "missing.csv", schedule)


def test_empty_real_results_template_fails_clearly() -> None:
    schedule = validate_schedule(ROOT / "tweet_schedule.csv")
    with pytest.raises(ValueError, match="expected at least one result row"):
        validate_results(ROOT / "data" / "real_experiment_results.csv", schedule)


def test_invalid_variant_fails(tmp_path: Path) -> None:
    schedule_path, results_path = copy_fixture(tmp_path)
    mutate_csv(results_path, lambda rows: rows[0].update({"variant": "C"}))
    schedule = validate_schedule(schedule_path)
    with pytest.raises(ValueError, match="variant must be A or B"):
        validate_results(results_path, schedule)


def test_duplicate_tweet_number_fails(tmp_path: Path) -> None:
    schedule_path, results_path = copy_fixture(tmp_path)
    mutate_csv(results_path, lambda rows: rows[1].update({"tweet_number": "1"}))
    schedule = validate_schedule(schedule_path)
    with pytest.raises(ValueError, match="duplicate tweet_number"):
        validate_results(results_path, schedule)


def test_negative_metric_fails(tmp_path: Path) -> None:
    schedule_path, results_path = copy_fixture(tmp_path)
    mutate_csv(results_path, lambda rows: rows[0].update({"likes": "-1"}))
    schedule = validate_schedule(schedule_path)
    with pytest.raises(ValueError, match="likes must be non-negative"):
        validate_results(results_path, schedule)


def test_metadata_mismatch_fails(tmp_path: Path) -> None:
    schedule_path, results_path = copy_fixture(tmp_path)
    mutate_csv(results_path, lambda rows: rows[0].update({"hook_text": "Changed"}))
    schedule = validate_schedule(schedule_path)
    with pytest.raises(ValueError, match="hook_text does not match"):
        validate_results(results_path, schedule)


def test_invalid_date_url_and_boolean_fail(tmp_path: Path) -> None:
    schedule_path, results_path = copy_fixture(tmp_path)
    schedule = validate_schedule(schedule_path)

    mutate_csv(results_path, lambda rows: rows[0].update({"posted_at": "not-a-date"}))
    with pytest.raises(ValueError, match="posted_at must be ISO-8601"):
        validate_results(results_path, schedule)

    _, results_path = copy_fixture(tmp_path)
    mutate_csv(results_path, lambda rows: rows[0].update({"tweet_url": "x-status"}))
    with pytest.raises(ValueError, match="tweet_url must be a valid URL"):
        validate_results(results_path, schedule)

    _, results_path = copy_fixture(tmp_path)
    mutate_csv(results_path, lambda rows: rows[0].update({"has_image": "maybe"}))
    with pytest.raises(ValueError, match="has_image must be true or false"):
        validate_results(results_path, schedule)


def test_schedule_requires_one_post_per_day(tmp_path: Path) -> None:
    schedule_path, _ = copy_fixture(tmp_path)
    mutate_csv(
        schedule_path,
        lambda rows: rows[1].update({"scheduled_at": rows[0]["scheduled_at"]}),
    )
    with pytest.raises(ValueError, match="one tweet per day"):
        validate_schedule(schedule_path)


def test_schedule_requires_same_posting_time(tmp_path: Path) -> None:
    schedule_path, _ = copy_fixture(tmp_path)
    mutate_csv(
        schedule_path,
        lambda rows: rows[0].update({"scheduled_at": "2026-06-01T18:00:00"}),
    )
    with pytest.raises(ValueError, match="all scheduled_at times"):
        validate_schedule(schedule_path)


def test_schedule_requires_topic_balance(tmp_path: Path) -> None:
    schedule_path, _ = copy_fixture(tmp_path)
    mutate_csv(schedule_path, lambda rows: rows[0].update({"topic": "analytics"}))
    with pytest.raises(ValueError, match="topic .* equal A/B"):
        validate_schedule(schedule_path)
