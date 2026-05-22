"""Streamlit dashboard for the creator A/B testing toolkit."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from experiment_analysis import analyze_experiment, load_config, load_results


st.set_page_config(
    page_title="Creator A/B Test",
    page_icon="AB",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1180px;
    }
    h1, h2, h3 {
        letter-spacing: 0;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.7rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_dashboard_data() -> tuple[dict, pd.DataFrame]:
    config = load_config()
    analysis = analyze_experiment(config)
    data = load_results(config.results_path, config.metric_columns, config.primary_metric)
    return analysis, data


def format_number(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def sample_share(data: pd.DataFrame) -> float:
    if "status" not in data.columns or data.empty:
        return 0.0
    return float((data["status"].astype(str).str.lower() == "sample").mean())


analysis, df = load_dashboard_data()
config = load_config()
comparison = analysis["comparison"]
recommendation = analysis["recommendation"]

st.title("Creator Experimentation Dashboard")
st.caption("A product experimentation framework applied to creator analytics")

share_sample = sample_share(df)
if share_sample > 0.5:
    st.warning(
        "This dashboard is currently using synthetic sample data. Replace it "
        "with data/real_experiment_results.csv before making real content decisions."
    )

overview_tab, design_tab, results_tab, evidence_tab, raw_tab = st.tabs(
    ["Overview", "Experiment Design", "Results", "Evidence", "Raw Data"]
)

control = comparison["control_variant"]
treatment = comparison["treatment_variant"]
control_mean = analysis["summary"][control]["mean"]
treatment_mean = analysis["summary"][treatment]["mean"]
lift = comparison["lift"]

with overview_tab:
    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric(
        f"{control} mean",
        f"{control_mean:.2f}",
        analysis["variant_labels"].get(control, control),
    )
    metric_2.metric(
        f"{treatment} mean",
        f"{treatment_mean:.2f}",
        analysis["variant_labels"].get(treatment, treatment),
    )
    metric_3.metric("Lift", f"{lift:.1%}")
    metric_4.metric("Decision", recommendation["status"].replace("_", " ").title())

    st.info(recommendation["message"])

    summary_df = (
        pd.DataFrame.from_dict(analysis["summary"], orient="index")
        .rename_axis("variant")
        .reset_index()
    )
    summary_df["label"] = summary_df["label"].astype(str)

    left, right = st.columns((1.1, 0.9))
    with left:
        st.subheader("Variant Comparison")
        st.bar_chart(summary_df, x="label", y="mean", color="#1f7a5a")

    with right:
        st.subheader("Statistical Readout")
        stats_rows = pd.DataFrame(
            [
                {"metric": "Welch p-value", "value": comparison["welch_ttest"]["p_value"]},
                {
                    "metric": "Mann-Whitney p-value",
                    "value": comparison["mann_whitney"]["p_value"],
                },
                {"metric": "Cohen's d", "value": comparison["cohens_d"]},
                {"metric": "Mean difference", "value": comparison["absolute_difference"]},
            ]
        )
        st.dataframe(stats_rows, hide_index=True, use_container_width=True)

with design_tab:
    st.subheader("Protocol")
    col_1, col_2, col_3, col_4 = st.columns(4)
    col_1.metric("Duration", "34 days")
    col_2.metric("Cadence", "1 post/day")
    col_3.metric("Post time", config.posting_time)
    col_4.metric("Metric window", f"{config.observation_window_hours}h")

    st.markdown(
        """
        This experiment uses stratified/block randomization. Every topic block
        contains one question-hook post and one statement-hook post. The
        validator enforces fixed posting time, consecutive dates, topic balance,
        image/no-image balance, and near-balanced weekday exposure.
        """
    )

    design_checks = pd.DataFrame(
        [
            {"control": "Total A/B count", "status": "17 A / 17 B"},
            {"control": "Posting time", "status": config.posting_time},
            {"control": "Frequency", "status": config.posting_frequency},
            {"control": "Randomization", "status": config.randomization_method},
            {"control": "Observation window", "status": f"{config.observation_window_hours} hours"},
        ]
    )
    st.dataframe(design_checks, hide_index=True, use_container_width=True)

    st.subheader("Topic and Media Balance")
    topic_balance = pd.crosstab(df["topic"], df["variant"])
    image_balance = pd.crosstab(df["has_image"], df["variant"])
    left, right = st.columns(2)
    left.dataframe(topic_balance, use_container_width=True)
    right.dataframe(image_balance, use_container_width=True)

with results_tab:
    st.subheader("Decision Explanation")
    ci = comparison["bootstrap_intervals"]["mean_difference"]
    lift_ci = comparison["bootstrap_intervals"]["lift"]
    st.markdown(
        f"""
        The recommendation is **{recommendation['status']}**.

        - Absolute difference: `{format_number(comparison['absolute_difference'])}`
        - Lift: `{lift:.1%}`
        - Bootstrap mean-difference CI: `[{format_number(ci['lower'])}, {format_number(ci['upper'])}]`
        - Bootstrap lift CI: `[{lift_ci['lower']:.1%}, {lift_ci['upper']:.1%}]`
        - Minimum practical lift threshold: `{config.minimum_practical_lift:.1%}`

        A winner is declared only when the confidence interval excludes zero and
        the lift clears the practical threshold.
        """
    )

    st.subheader("Engagement Distribution")
    distribution = df[["variant", config.primary_metric]].rename(
        columns={config.primary_metric: "engagement"}
    )
    st.bar_chart(distribution, x="variant", y="engagement", color="#2563eb")

    st.subheader("Cumulative Engagement")
    cumulative = df.sort_values("tweet_number").copy()
    cumulative["cumulative_engagement"] = cumulative.groupby("variant")[
        config.primary_metric
    ].cumsum()
    st.line_chart(
        cumulative,
        x="tweet_number",
        y="cumulative_engagement",
        color="variant",
    )

    metric_breakdown = (
        df.groupby("variant")[config.metric_columns]
        .sum()
        .reset_index()
        .melt(id_vars="variant", var_name="metric", value_name="count")
    )
    st.subheader("Metric Breakdown")
    st.bar_chart(metric_breakdown, x="metric", y="count", color="variant")

with evidence_tab:
    st.subheader("Post Evidence")
    evidence_dir = Path("data/post_evidence")
    image_paths = sorted(
        path
        for pattern in ("*.png", "*.jpg", "*.jpeg", "*.webp")
        for path in evidence_dir.glob(pattern)
    )

    if not image_paths:
        st.info(
            "No real post screenshots have been added yet. Add screenshots to "
            "data/post_evidence/ after the real 34-day experiment is complete."
        )
    else:
        for image_path in image_paths:
            st.image(str(image_path), caption=image_path.name, use_container_width=True)

    st.markdown(
        """
        Evidence screenshots should show the public post, hook text, timestamp,
        and visible engagement counts so the case study can be audited.
        """
    )

with raw_tab:
    st.subheader("Rows")
    st.dataframe(
        df[
            [
                "tweet_number",
                "variant",
                "scheduled_at",
                "posted_at",
                "topic",
                "hook_text",
                *config.metric_columns,
                config.primary_metric,
                "status",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )
