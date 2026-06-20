# Creator Experimentation Toolkit

A product experimentation framework applied to creator analytics.

This project shows how A/B testing practices from product analytics can be used
to test creator-content decisions with controlled assignment, validation,
statistical testing, reports, and a dashboard.

## Project Snapshot

| | |
|---|---|
| **Business problem** | Test whether question-based or statement-based hooks improve creator engagement without relying on noisy post-to-post comparisons. |
| **Quantified result** | In the **synthetic demo data**, statement hooks averaged **9.18** engagements versus **4.24** for question hooks: **+116.7% lift**, with a bootstrap lift interval of **81.2% to 159.7%**. |
| **Method** | 34-day stratified assignment, balance validation, Welch and Mann-Whitney tests, Cohen's d, bootstrap confidence intervals, and a predeclared decision rule. |
| **Demo** | Run `streamlit run app.py` for the Overview, Experiment Design, Results, Evidence, and Raw Data views. |
| **Limitations** | The committed results are synthetic and the 34-post design is small; real recommendations require real posts collected under the fixed protocol. |
| **Reproduce** | `pip install -r requirements.txt` → `python validate_experiment.py` → `python analyze_experiment.py` → `streamlit run app.py`. |

## Why This Exists

X Analytics reports what happened to each post. This project tests whether a
specific controlled change likely caused a difference.

The current experiment compares:

- Variant A: question-based hooks
- Variant B: statement-based hooks

The committed `data/experiment_results.csv` file is synthetic sample data so the
project runs from a fresh clone. Use `data/real_experiment_results.csv` for real
tweet metrics before making real recommendations.

## What This Project Does

- Builds a deterministic 34-day stratified/block-randomized schedule.
- Controls avoidable bias from posting time, topic, media usage, and weekday mix.
- Validates schedule and result files before analysis.
- Computes engagement from likes, replies, reposts, and bookmarks.
- Reports Welch's t-test, Mann-Whitney U test, Cohen's d, lift, and bootstrap
  confidence intervals.
- Applies a predeclared decision rule so the winner is not chosen by vibes.
- Exports Markdown and JSON reports.
- Provides a Streamlit dashboard for portfolio-ready exploration.
- Documents a safe manual-first data ingestion path and an official API scaffold.

## Resume Highlights

- Built a reproducible A/B testing toolkit for creator analytics using Python,
  pandas, scipy, Streamlit, and pytest.
- Designed a 34-day stratified experiment controlling for posting time, topic,
  media usage, and weekday bias.
- Implemented automated validation for experiment schema, randomization balance,
  metric integrity, and schedule/result consistency.
- Added Welch's t-test, Mann-Whitney U test, Cohen's d, bootstrap confidence
  intervals, and decision rules for winner selection.
- Built a Streamlit dashboard and CLI reports to communicate experiment results
  and statistical uncertainty.

## Repository Structure

```text
.
|-- app.py
|-- analyze_experiment.py
|-- experiment_analysis.py
|-- experiment_config.json
|-- validate_experiment.py
|-- case_study.md
|-- tweet_schedule.csv
|-- data/
|   |-- experiment_results.csv
|   |-- real_experiment_results.csv
|   `-- post_evidence/
|-- data_ingestion/
|   |-- README.md
|   `-- x_api_ingest_stub.py
|-- reports/
|-- tests/
|-- .github/workflows/ci.yml
|-- Analysis.ipynb
|-- Power Analysis.ipynb
|-- bayesian_analysis.ipynb
|-- randomization.ipynb
`-- thompson_sampling.ipynb
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

## Core Workflow

1. Edit `experiment_config.json` if the experiment name, variants, thresholds,
   or file paths change.
2. Use `tweet_schedule.csv` to plan the 34 posts.
3. Post one tweet per day at the same chosen peak time.
4. Record metrics after the same observation window, configured as 48 hours.
5. Fill `data/real_experiment_results.csv` with real metrics.
6. Add real post screenshots under `data/post_evidence/`.
7. Validate the real data:

```bash
python validate_experiment.py --results data/real_experiment_results.csv
```

8. Analyze the real data:

```bash
python analyze_experiment.py --results data/real_experiment_results.csv
```

9. Open the dashboard:

```bash
streamlit run app.py
```

For demo/sample mode, use:

```bash
python validate_experiment.py
python analyze_experiment.py
```

## Deploy On Streamlit Cloud

This app is ready for Streamlit Community Cloud in demo mode. It uses the
committed synthetic sample data by default, so no secrets or API keys are
required for the public dashboard.

Use these settings:

- Repository: `Vatsalsrivastava1209/Creator-Experimentation-Toolkit`
- Branch: `main`
- Main file path: `app.py`
- Python runtime: `python-3.11` from `runtime.txt`
- Secrets: none required for sample/demo mode

After deployment, confirm the app shows the Overview, Experiment Design,
Results, Evidence, and Raw Data tabs. The synthetic-data warning should remain
visible until real X metrics replace the sample results.

## Data Contract

Both `tweet_schedule.csv` and results files use this schema:

```csv
tweet_number,variant,scheduled_at,posted_at,tweet_id,tweet_url,hook_text,topic,content_type,is_thread,has_image,likes,replies,reposts,bookmarks,status
```

Validation rules:

- `tweet_number` must be a positive integer and unique.
- `variant` must be `A` or `B`.
- `scheduled_at` and `posted_at`, when present, must be ISO-8601 datetimes.
- `tweet_url`, when present, must be a valid `http` or `https` URL.
- `is_thread` and `has_image` must be `true` or `false`.
- Engagement metrics must be integer-like, non-null, and non-negative in the
  results file.
- Result rows must match the scheduled assignment and metadata.
- The schedule must contain one tweet per day across 34 consecutive days.
- Every scheduled post must use the same posting time, currently `09:00:00`.
- Topics and image/no-image strata must have equal A/B counts.
- Day-of-week A/B counts must differ by no more than one.

## Experiment Protocol

The schedule uses stratified/block randomization instead of a plain shuffle:

- 34 total days
- one tweet per day
- one fixed peak posting time
- 17 question-hook tweets and 17 statement-hook tweets
- each topic block has one A and one B post
- image/no-image conditions are balanced across A and B
- weekday exposure is balanced as closely as mathematically possible
- metrics are recorded after a fixed 48-hour observation window

This reduces avoidable bias from posting time, topic mix, media format, and
day-of-week effects.

## Analysis Outputs

`python analyze_experiment.py` writes:

- `reports/analysis_summary.json`
- `reports/analysis_summary.md`

The report includes sample size, mean, median, standard deviation, lift,
Welch's t-test, Mann-Whitney U test, Cohen's d, bootstrap confidence intervals,
and recommendation status.

## Data Ingestion Positioning

Manual CSV entry is the default and safest path. Scraping is intentionally
unsupported because it can be brittle, violate platform expectations, and create
account risk. Official X API ingestion can be added later for users with
approved credentials; see `data_ingestion/`.

## Case Study

Read `case_study.md` for the portfolio narrative:

- hypothesis
- design
- bias controls
- data collection protocol
- methods
- results
- recommendation
- limitations
- next test

## Limitations

- The committed result rows are synthetic sample data.
- A 34-post experiment is useful for learning, but confidence intervals can
  still be wide.
- Engagement counts are skewed and sensitive to timing, topic, audience mood,
  and platform distribution.
- The analysis identifies evidence for this experiment only. It does not prove
  that one hook style will always win.

## Author

Vatsal

LinkedIn: https://www.linkedin.com/in/vatsal-srivastava-440417260/
