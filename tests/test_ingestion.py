from __future__ import annotations

import csv
from pathlib import Path

from data_ingestion.x_api_ingest_stub import OUTPUT_COLUMNS, write_empty_template


def test_x_api_stub_writes_validator_compatible_header(tmp_path: Path) -> None:
    output_path = tmp_path / "real_experiment_results.csv"
    write_empty_template(output_path)

    with output_path.open(newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader)

    assert header == OUTPUT_COLUMNS
