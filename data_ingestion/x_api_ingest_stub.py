"""Official X API ingestion scaffold.

This file documents where safe API ingestion would live. It does not scrape X,
does not call the API, and does not require credentials to import.

Expected environment variables for a future implementation:

- X_BEARER_TOKEN
- X_USER_ID

The future implementation should write rows using the same schema as
data/real_experiment_results.csv, then run validate_experiment.py before
analysis.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


OUTPUT_COLUMNS = [
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
]


def write_empty_template(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/real_experiment_results.csv", type=Path)
    parser.add_argument(
        "--write-template",
        action="store_true",
        help="Write an empty real-results CSV template without calling the X API.",
    )
    args = parser.parse_args()

    if args.write_template:
        write_empty_template(args.output)
        print(f"Wrote empty template to {args.output}")
        return 0

    print(
        "Official X API ingestion is intentionally a scaffold. "
        "Use --write-template for the CSV template, or implement API calls with "
        "approved X API credentials."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
