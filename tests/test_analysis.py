from __future__ import annotations

from pathlib import Path
import shutil

from experiment_analysis import analyze_experiment, bootstrap_intervals, load_config


ROOT = Path(__file__).resolve().parents[1]


def test_analysis_has_required_outputs() -> None:
    config = load_config(ROOT / "experiment_config.json")
    analysis = analyze_experiment(config, ROOT / "data" / "experiment_results.csv")

    comparison = analysis["comparison"]
    assert set(analysis["summary"]) == {"A", "B"}
    assert comparison["welch_ttest"]["p_value"] is not None
    assert comparison["mann_whitney"]["p_value"] is not None
    assert comparison["bootstrap_intervals"]["mean_difference"]["lower"] is not None
    assert analysis["recommendation"]["status"] in {
        "winner",
        "inconclusive",
        "insufficient_data",
    }


def test_bootstrap_intervals_are_reproducible() -> None:
    control = [1, 2, 3, 4]
    treatment = [3, 4, 5, 6]
    first = bootstrap_intervals(control, treatment, iterations=200, seed=42, alpha=0.05)
    second = bootstrap_intervals(control, treatment, iterations=200, seed=42, alpha=0.05)
    assert first == second
    assert set(first) == {"mean_difference", "lift"}


def test_sample_data_produces_deterministic_lift() -> None:
    config = load_config(ROOT / "experiment_config.json")
    analysis = analyze_experiment(config, ROOT / "data" / "experiment_results.csv")
    assert round(analysis["comparison"]["lift"], 4) == 1.1667


def test_analysis_accepts_alternate_results_path(tmp_path: Path) -> None:
    config = load_config(ROOT / "experiment_config.json")
    alternate_results = tmp_path / "alternate_results.csv"
    shutil.copy(ROOT / "data" / "experiment_results.csv", alternate_results)

    analysis = analyze_experiment(config, alternate_results)

    assert analysis["summary"]["A"]["count"] == 17
    assert analysis["summary"]["B"]["count"] == 17
