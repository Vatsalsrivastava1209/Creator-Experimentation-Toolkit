"""Reusable analysis helpers for creator A/B test experiments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_name: str
    variant_labels: dict[str, str]
    metric_columns: list[str]
    primary_metric: str
    control_variant: str
    treatment_variant: str
    alpha: float
    bootstrap_iterations: int
    random_seed: int
    randomization_method: str
    posting_time: str
    posting_frequency: str
    observation_window_hours: int
    minimum_sample_size_per_variant: int
    minimum_practical_lift: float
    schedule_path: str
    results_path: str
    report_json_path: str
    report_markdown_path: str


def load_config(path: str | Path = "experiment_config.json") -> ExperimentConfig:
    with Path(path).open(encoding="utf-8") as file:
        raw = json.load(file)
    return ExperimentConfig(**raw)


def load_results(
    results_path: str | Path,
    metric_columns: list[str],
    primary_metric: str,
) -> pd.DataFrame:
    df = pd.read_csv(results_path)
    if df.empty:
        raise ValueError(f"{results_path} has no result rows to analyze")
    for column in metric_columns:
        df[column] = pd.to_numeric(df[column], errors="raise")
    df[primary_metric] = df[metric_columns].sum(axis=1)
    return df


def group_summaries(
    df: pd.DataFrame,
    metric: str,
    variant_labels: dict[str, str],
) -> dict[str, dict[str, Any]]:
    grouped = df.groupby("variant")[metric]
    summary = grouped.agg(["count", "mean", "median", "std", "sum"]).round(4)

    result: dict[str, dict[str, Any]] = {}
    for variant, row in summary.iterrows():
        result[str(variant)] = {
            "label": variant_labels.get(str(variant), str(variant)),
            "count": int(row["count"]),
            "mean": float(row["mean"]),
            "median": float(row["median"]),
            "std": None if pd.isna(row["std"]) else float(row["std"]),
            "total": float(row["sum"]),
        }
    return result


def _variant_values(
    df: pd.DataFrame,
    metric: str,
    control_variant: str,
    treatment_variant: str,
) -> tuple[np.ndarray, np.ndarray]:
    control = df.loc[df["variant"] == control_variant, metric].to_numpy(dtype=float)
    treatment = df.loc[df["variant"] == treatment_variant, metric].to_numpy(dtype=float)
    return control, treatment


def welch_ttest(control: np.ndarray, treatment: np.ndarray) -> dict[str, float | None]:
    if len(control) < 2 or len(treatment) < 2:
        return {"statistic": None, "p_value": None}
    statistic, p_value = stats.ttest_ind(
        control,
        treatment,
        equal_var=False,
        nan_policy="raise",
    )
    return {"statistic": float(statistic), "p_value": float(p_value)}


def mann_whitney(control: np.ndarray, treatment: np.ndarray) -> dict[str, float | None]:
    if len(control) < 1 or len(treatment) < 1:
        return {"statistic": None, "p_value": None}
    statistic, p_value = stats.mannwhitneyu(
        control,
        treatment,
        alternative="two-sided",
    )
    return {"statistic": float(statistic), "p_value": float(p_value)}


def effect_size(control: np.ndarray, treatment: np.ndarray) -> float | None:
    if len(control) < 2 or len(treatment) < 2:
        return None
    pooled_std = np.sqrt((np.var(control, ddof=1) + np.var(treatment, ddof=1)) / 2)
    if pooled_std == 0:
        return None
    return float((np.mean(treatment) - np.mean(control)) / pooled_std)


def bootstrap_intervals(
    control: np.ndarray,
    treatment: np.ndarray,
    iterations: int,
    seed: int,
    alpha: float,
) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    control = np.asarray(control, dtype=float)
    treatment = np.asarray(treatment, dtype=float)
    if len(control) == 0 or len(treatment) == 0:
        raise ValueError("Both variants need at least one row for bootstrap analysis")

    mean_diffs = np.empty(iterations)
    lifts = np.empty(iterations)

    for index in range(iterations):
        control_sample = rng.choice(control, size=len(control), replace=True)
        treatment_sample = rng.choice(treatment, size=len(treatment), replace=True)
        control_mean = np.mean(control_sample)
        treatment_mean = np.mean(treatment_sample)

        mean_diffs[index] = treatment_mean - control_mean
        lifts[index] = np.nan if control_mean == 0 else mean_diffs[index] / control_mean

    lower = 100 * (alpha / 2)
    upper = 100 * (1 - alpha / 2)

    return {
        "mean_difference": {
            "lower": float(np.nanpercentile(mean_diffs, lower)),
            "upper": float(np.nanpercentile(mean_diffs, upper)),
        },
        "lift": {
            "lower": float(np.nanpercentile(lifts, lower)),
            "upper": float(np.nanpercentile(lifts, upper)),
        },
    }


def make_recommendation(
    control_count: int,
    treatment_count: int,
    lift: float | None,
    mean_difference_ci: dict[str, float],
    config: ExperimentConfig,
) -> dict[str, Any]:
    if (
        control_count < config.minimum_sample_size_per_variant
        or treatment_count < config.minimum_sample_size_per_variant
    ):
        return {
            "status": "insufficient_data",
            "winner_variant": None,
            "message": (
                "Collect more results before choosing a winner. "
                f"Minimum required per variant: {config.minimum_sample_size_per_variant}."
            ),
        }

    if lift is None:
        return {
            "status": "inconclusive",
            "winner_variant": None,
            "message": "Lift could not be computed because the control mean is zero.",
        }

    ci_excludes_zero = (
        mean_difference_ci["lower"] > 0 or mean_difference_ci["upper"] < 0
    )
    practical = abs(lift) >= config.minimum_practical_lift

    if ci_excludes_zero and practical and lift > 0:
        return {
            "status": "winner",
            "winner_variant": config.treatment_variant,
            "message": (
                f"Variant {config.treatment_variant} clears the statistical and "
                "practical thresholds."
            ),
        }

    if ci_excludes_zero and practical and lift < 0:
        return {
            "status": "winner",
            "winner_variant": config.control_variant,
            "message": (
                f"Variant {config.control_variant} clears the statistical and "
                "practical thresholds."
            ),
        }

    return {
        "status": "inconclusive",
        "winner_variant": None,
        "message": (
            "No winner yet. The confidence interval and practical lift threshold "
            "do not both support a decision."
        ),
    }


def analyze_experiment(
    config: ExperimentConfig,
    results_path: str | Path | None = None,
) -> dict[str, Any]:
    path = results_path or config.results_path
    df = load_results(path, config.metric_columns, config.primary_metric)
    control, treatment = _variant_values(
        df,
        config.primary_metric,
        config.control_variant,
        config.treatment_variant,
    )

    control_mean = float(np.mean(control)) if len(control) else None
    treatment_mean = float(np.mean(treatment)) if len(treatment) else None
    mean_difference = (
        None
        if control_mean is None or treatment_mean is None
        else treatment_mean - control_mean
    )
    lift = (
        None
        if mean_difference is None or control_mean == 0
        else mean_difference / control_mean
    )

    intervals = bootstrap_intervals(
        control,
        treatment,
        config.bootstrap_iterations,
        config.random_seed,
        config.alpha,
    )

    return {
        "experiment_name": config.experiment_name,
        "primary_metric": config.primary_metric,
        "variant_labels": config.variant_labels,
        "summary": group_summaries(df, config.primary_metric, config.variant_labels),
        "comparison": {
            "control_variant": config.control_variant,
            "treatment_variant": config.treatment_variant,
            "absolute_difference": mean_difference,
            "lift": lift,
            "welch_ttest": welch_ttest(control, treatment),
            "mann_whitney": mann_whitney(control, treatment),
            "cohens_d": effect_size(control, treatment),
            "bootstrap_intervals": intervals,
        },
        "recommendation": make_recommendation(
            len(control),
            len(treatment),
            lift,
            intervals["mean_difference"],
            config,
        ),
    }


def to_markdown_report(analysis: dict[str, Any]) -> str:
    comparison = analysis["comparison"]
    recommendation = analysis["recommendation"]

    def fmt(value: float | None, digits: int = 3) -> str:
        return "n/a" if value is None else f"{value:.{digits}f}"

    def fmt_pct(value: float | None, digits: int = 3) -> str:
        return "n/a" if value is None else f"{value:.{digits}%}"

    lines = [
        f"# {analysis['experiment_name']} Analysis",
        "",
        f"Primary metric: `{analysis['primary_metric']}`",
        "",
        "## Variant Summary",
        "",
        "| Variant | Label | N | Mean | Median | Std | Total |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for variant, row in sorted(analysis["summary"].items()):
        std = "" if row["std"] is None else f"{row['std']:.3f}"
        lines.append(
            f"| {variant} | {row['label']} | {row['count']} | "
            f"{row['mean']:.3f} | {row['median']:.3f} | {std} | {row['total']:.0f} |"
        )

    ci = comparison["bootstrap_intervals"]["mean_difference"]
    lift_ci = comparison["bootstrap_intervals"]["lift"]
    lines.extend(
        [
            "",
            "## Comparison",
            "",
            f"- Absolute difference: {fmt(comparison['absolute_difference'])}",
            f"- Lift: {fmt_pct(comparison['lift'])}",
            f"- Welch p-value: {fmt(comparison['welch_ttest']['p_value'], 4)}",
            f"- Mann-Whitney p-value: {fmt(comparison['mann_whitney']['p_value'], 4)}",
            f"- Cohen's d: {fmt(comparison['cohens_d'])}",
            (
                "- Bootstrap mean-difference CI: "
                f"[{ci['lower']:.3f}, {ci['upper']:.3f}]"
            ),
            f"- Bootstrap lift CI: [{lift_ci['lower']:.3%}, {lift_ci['upper']:.3%}]",
            "",
            "## Recommendation",
            "",
            f"**{recommendation['status']}**",
            "",
            recommendation["message"],
            "",
        ]
    )
    return "\n".join(lines)
