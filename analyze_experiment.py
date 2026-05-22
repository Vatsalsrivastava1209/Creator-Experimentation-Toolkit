"""Run the creator A/B test analysis and write report artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from experiment_analysis import analyze_experiment, load_config, to_markdown_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="experiment_config.json", type=Path)
    parser.add_argument("--schedule", default=None, type=Path)
    parser.add_argument("--results", default=None, type=Path)
    args = parser.parse_args()

    config = load_config(args.config)
    results_path = args.results or config.results_path
    try:
        analysis = analyze_experiment(config, results_path=results_path)
    except ValueError as exc:
        print(f"Analysis failed: {exc}", file=sys.stderr)
        return 1

    json_path = Path(config.report_json_path)
    markdown_path = Path(config.report_markdown_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    markdown_path.write_text(to_markdown_report(analysis), encoding="utf-8")

    recommendation = analysis["recommendation"]
    comparison = analysis["comparison"]
    print(f"Experiment: {analysis['experiment_name']}")
    print(f"Primary metric: {analysis['primary_metric']}")
    print(f"Lift: {comparison['lift']:.2%}")
    print(f"Welch p-value: {comparison['welch_ttest']['p_value']:.4f}")
    print(f"Recommendation: {recommendation['status']} - {recommendation['message']}")
    print(f"Wrote {json_path} and {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
