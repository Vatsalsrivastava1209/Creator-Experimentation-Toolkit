# Data Ingestion

Metric collection is manual by default. This is intentional: X can restrict,
rate-limit, or ban accounts that rely on brittle scraping, and official API
access may be paid or limited.

## Supported Modes

1. Manual CSV entry
   - Fill `data/real_experiment_results.csv` after each post reaches the fixed
     observation window.
   - Run `python validate_experiment.py --results data/real_experiment_results.csv`.
   - This is the safest default and the recommended portfolio workflow.

2. Official X API
   - Use only if you have approved X API access.
   - Export rows using the same schema as `data/real_experiment_results.csv`.
   - Run the same validator before analysis.

3. Scraping
   - Intentionally unsupported.
   - Scrapers are fragile, may violate platform expectations, and can create
     account risk.

## Required Output Schema

Any ingestion source must write this header exactly:

```csv
tweet_number,variant,scheduled_at,posted_at,tweet_id,tweet_url,hook_text,topic,content_type,is_thread,has_image,likes,replies,reposts,bookmarks,status
```

The validator remains the quality gate for manual and API-driven ingestion.
