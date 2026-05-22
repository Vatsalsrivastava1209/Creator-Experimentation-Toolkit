# Case Study: Product Experimentation for Creator Analytics

## Current Status

This case study currently uses synthetic sample data so the repository can run
from a fresh clone. Real conclusions should not be drawn until
`data/real_experiment_results.csv` is filled with actual X post metrics and
supported with screenshots in `data/post_evidence/`.

## Hypothesis

Question-based tweet hooks will produce higher engagement than statement-based
tweet hooks because questions can create curiosity and invite replies.

## Experiment Design

- 34 total posts
- 17 question-hook posts
- 17 statement-hook posts
- one post per day
- fixed posting time: 09:00
- fixed observation window: 48 hours
- primary metric: engagement
- engagement formula: likes + replies + reposts + bookmarks

## Bias Controls

The schedule uses stratified/block randomization instead of a plain shuffle:

- every topic block contains one A row and one B row
- image/no-image conditions are balanced across A and B
- day-of-week exposure is balanced within one post
- all posts use the same scheduled time
- validation fails if these constraints are broken

## Data Collection Protocol

1. Publish one scheduled post per day.
2. Wait for the configured 48-hour observation window.
3. Record `posted_at`, `tweet_id`, `tweet_url`, likes, replies, reposts, and
   bookmarks in `data/real_experiment_results.csv`.
4. Add a screenshot for each real post under `data/post_evidence/`.
5. Run `python validate_experiment.py --results data/real_experiment_results.csv`.
6. Run `python analyze_experiment.py --results data/real_experiment_results.csv`.

## Statistical Methods

- Welch's t-test compares average engagement while allowing unequal variance.
- Mann-Whitney U test provides a rank-based robustness check for skewed counts.
- Cohen's d reports practical effect size.
- Bootstrap confidence intervals estimate uncertainty around lift.
- The decision rule declares a winner only when the confidence interval excludes
  zero and the lift clears the configured practical threshold.

## Results

The committed report uses synthetic sample data:

- report: `reports/analysis_summary.md`
- dashboard: `streamlit run app.py`

Real results should be summarized here after the 34-day experiment completes.

## Recommendation

Current recommendation is demo-only because sample data is synthetic. With real
data, the recommendation should state whether variant A, variant B, or neither
clears the predeclared decision rule.

## Limitations

- Social engagement is noisy and affected by platform distribution.
- A 34-post experiment can still have wide confidence intervals.
- The experiment estimates performance for one account and one time period.
- X Analytics can report post performance, but this project adds controlled
  assignment, validation, statistical testing, and decision rules.

## Next Test

After the hook-style experiment, test one higher-business-value content lever,
such as:

- technical tutorial vs career advice
- single post vs short thread
- text-only vs visual post
- morning vs evening posting time in a separately designed experiment

## Impact Summary

Built a reusable product experimentation workflow for creator analytics,
including stratified experimental design, automated data validation, statistical
analysis, CLI reporting, and a Streamlit dashboard. The project demonstrates how
product analytics methods can be adapted to creator growth decisions without
relying on risky scraping or unvalidated dashboard screenshots.
