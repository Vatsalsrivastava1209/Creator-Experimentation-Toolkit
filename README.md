# Tweet Experiment: A/B Testing on X

## Overview

This project is a notebook-first A/B testing workflow for measuring whether
question-based tweet hooks outperform statement-based tweet hooks on an X
(Twitter) creator account.

The repo demonstrates a reproducible experimentation flow:

- power analysis
- randomized assignment
- metric collection
- input validation
- frequentist analysis
- optional Bayesian and Thompson sampling analysis

## Hypothesis

If tweets start with a question hook, then engagement will increase compared
with a statement hook because questions can trigger curiosity and encourage
replies.

## Repository Structure

```text
.
|-- Analysis.ipynb
|-- Power Analysis.ipynb
|-- bayesian_analysis.ipynb
|-- randomization.ipynb
|-- thompson_sampling.ipynb
|-- data/
|   `-- experiment_results.csv
|-- requirements.txt
|-- tweet_schedule.csv
`-- validate_experiment.py
```

The committed `data/experiment_results.csv` is synthetic sample data so the
notebooks and validator can run from a fresh clone. Replace it with real tweet
metrics before drawing conclusions.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

## Workflow

1. Run `Power Analysis.ipynb` to confirm the target sample size.
2. Run `randomization.ipynb` to generate a deterministic tweet schedule.
3. Post tweets according to `tweet_schedule.csv`.
4. Replace `data/experiment_results.csv` with real results using this schema:

```csv
tweet_number,variant,likes,replies,reposts,bookmarks
1,A,3,1,0,0
2,B,5,2,1,0
```

5. Validate the schedule and results:

```bash
python validate_experiment.py
```

6. Run `Analysis.ipynb` for the primary Welch's t-test analysis.
7. Optionally run `bayesian_analysis.ipynb` and `thompson_sampling.ipynb`.

## Data Contract

`data/experiment_results.csv` must include:

- `tweet_number`: positive integer, unique, and present in `tweet_schedule.csv`
- `variant`: `A` or `B`, matching the scheduled assignment
- `likes`: non-negative integer-like value
- `replies`: non-negative integer-like value
- `reposts`: non-negative integer-like value
- `bookmarks`: non-negative integer-like value

Optional future columns include `tweet_id`, `posted_at`, `scheduled_at`,
`content_id`, and `status`.

Engagement is calculated consistently as:

```python
df["engagement"] = (
    df["likes"] + df["replies"] + df["reposts"] + df["bookmarks"]
)
```

## Statistical Analysis

The primary analysis compares mean engagement between variants with Welch's
two-sample t-test:

- `p < 0.05`: statistically significant difference
- `p >= 0.05`: no statistically significant difference

The analysis notebook also reports group counts, means, confidence intervals,
and effect size so the result is not interpreted from p-value alone.

## Limitations

- The experiment has a small sample size of 34 tweets.
- Tweet engagement is noisy and can be affected by time of day, topic,
  audience availability, and platform distribution.
- Engagement counts are skewed discrete outcomes, so the t-test should be read
  alongside effect size, confidence intervals, and the optional Bayesian view.
- The sample results file is not evidence about the real account.

## Author

Vatsal

LinkedIn: https://www.linkedin.com/in/vatsal-srivastava-440417260/
