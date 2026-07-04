# Project Insights

A Data Engineering + Data Analytics platform that tracks how movie and TV show popularity, ratings, and vote counts change over time — built because TMDB shows today's popularity score but keeps no history of it.

**Live Dashboard:** [Add your Streamlit Cloud URL here]

---

## The Problem

TMDB (The Movie Database) exposes a real-time popularity score for every title, but provides no way to see how that score changes over time. This project fills that gap by capturing a daily snapshot of popularity, rating, and vote count for **10,449 movies** and **10,332 TV shows**, building an original time-series dataset from scratch that doesn't exist anywhere publicly.

## Architecture

```
TMDB API → AWS Lambda (Python, threaded) → AWS S3 → AWS Athena → Streamlit Dashboard
                                                ↑
                                        AWS EventBridge (nightly scheduler)
```

- **Ingestion:** 3 Lambda functions fetch daily metrics from TMDB using `ThreadPoolExecutor` (20 parallel workers) to stay within Lambda's 15-minute timeout. TV shows are split across two parallel Lambdas since the `/tv/{id}` endpoint is ~3x slower than `/movie/{id}`.
- **Storage:** S3, using Hive-style partitioning (`snapshot_date=YYYY-MM-DD`) so Athena only scans the date ranges a query actually needs, keeping query cost flat as the dataset grows.
- **Query layer:** Athena (Trino engine) queries CSVs directly on S3 — no database server to manage. Partitions are registered via `ALTER TABLE ADD PARTITION` (not `MSCK REPAIR`, which is unreliable at this data volume).
- **Processing:** A dedicated processor Lambda runs 14 pre-aggregation queries nightly (top 10, 7-day gainers/losers, by-year trends, genre ratings, language distribution, top voted) and writes the results as CSVs to a `processed/` folder — so the live dashboard reads flat files via boto3 instead of hitting Athena on every page load.
- **Scheduling:** EventBridge triggers all Lambdas nightly, in UTC (a timezone misconfiguration in IST previously caused a missed run — UTC is used everywhere now for reliability).
- **Dashboard:** Streamlit Cloud, auto-deployed from this repo, using a two-tier fetch strategy — pre-computed CSVs for static views, live Athena queries only for interactive features (Trend Explorer, Head-to-Head comparison).

## Tech Stack

| Layer | Technology |
|---|---|
| Compute | AWS Lambda (Python 3.12) |
| Storage | AWS S3 |
| Query Engine | AWS Athena (Trino) |
| Metadata Catalog | AWS Glue Data Catalog |
| Scheduling | AWS EventBridge |
| Dashboard | Streamlit + Plotly |
| Language | Python |
| Libraries | pandas, boto3, requests, pyathena |

## Key Engineering Decisions

- **Threaded fetching:** sequential API calls for ~10,000 IDs took 3.5+ hours; `ThreadPoolExecutor` with 20 workers brought this down to ~10 minutes.
- **Split TV pipeline:** the TV endpoint's latency meant a single Lambda would exceed the 15-minute hard limit — solved by splitting IDs into two halves running in parallel.
- **Partition-based Athena queries:** without partitioning, every query would scan the entire historical dataset, growing more expensive daily. Hive-style partitioning keeps query cost constant.
- **Pre-computed dashboard reads:** running Athena queries on every dashboard page load would be slow and costly at scale. A nightly processor Lambda pre-computes all standard views; only genuinely dynamic user queries (search, comparison) hit Athena live.
- **Infrastructure durability:** credentials are never hardcoded — Lambda uses IAM roles, and all secrets (AWS keys, TMDB API key) are managed via environment variables and Streamlit Cloud secrets, never committed to source control.

## Data

- 10,449 movies tracked (2020–2026)
- 10,332 TV shows tracked (2020–2026)
- ~10,430 rows/day (movies), ~10,303 rows/day (TV)
- Daily snapshots since re-launch in July 2026

## Local Setup

```bash
git clone https://github.com/StaticQuake/project-insight-v2.git
cd project-insight-v2
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` with your own AWS credentials (see `.streamlit/secrets.toml.example` if provided):

```toml
[aws]
aws_access_key_id = "your-access-key-id"
aws_secret_access_key = "your-secret-access-key"
region_name = "ap-south-1"
bucket_name = "your-bucket-name"
```

Then run:

```bash
streamlit run streamlit_app.py
```

## Project Status

Actively maintained. Originally built as a Semester 6 mini project (B.E. AI & Data Science, Mumbai University); rebuilt on a fresh AWS account in July 2026 with hardened credential handling and infrastructure documentation.