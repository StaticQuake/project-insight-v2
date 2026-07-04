import boto3
import pandas as pd
import io
import os
from datetime import date, timedelta

BUCKET = os.environ['BUCKET']
ATHENA_RESULTS = f's3://{BUCKET}/athena-results/'
DATABASE = os.environ.get('DATABASE', 'project_insights')
REGION = os.environ.get('AWS_REGION_NAME', 'ap-south-1')

s3 = boto3.client('s3', region_name=REGION)
athena = boto3.client('athena', region_name=REGION)

#process
# ── Athena helpers ────────────────────────────────────────────────────────────

def run_query(sql):
    """Run Athena query and return results as DataFrame."""
    resp = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={'Database': DATABASE},
        ResultConfiguration={'OutputLocation': ATHENA_RESULTS}
    )
    qid = resp['QueryExecutionId']

    # Wait for completion
    import time
    for _ in range(60):
        status = athena.get_query_execution(QueryExecutionId=qid)
        state = status['QueryExecution']['Status']['State']
        if state == 'SUCCEEDED':
            break
        if state in ('FAILED', 'CANCELLED'):
            reason = status['QueryExecution']['Status'].get('StateChangeReason', '')
            raise Exception(f'Athena query failed: {reason}')
        time.sleep(3)
    else:
        raise Exception('Athena query timed out after 3 minutes')

    # Get result location and read it
    result_loc = status['QueryExecution']['ResultConfiguration']['OutputLocation']
    key = result_loc.replace(f's3://{BUCKET}/', '')
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    return pd.read_csv(io.BytesIO(obj['Body'].read()))


def save_to_processed(df, filename):
    """Save DataFrame as CSV to processed/ folder."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    s3.put_object(
        Bucket=BUCKET,
        Key=f'processed/{filename}',
        Body=buf.getvalue(),
        ContentType='text/csv'
    )
    print(f'  Saved processed/{filename} ({len(df)} rows)')


# ── Movies aggregations ───────────────────────────────────────────────────────

def process_movies():
    print('Processing movies...')

    # 1. Top 10 most popular today
    top10 = run_query("""
        SELECT m.title, m.release_year, d.popularity, d.vote_average, d.vote_count,
               CONCAT(m.title, ' (', CAST(m.release_year AS VARCHAR), ')') as display_title
        FROM daily_metrics d
        JOIN movies_master m ON d.id = m.id
        WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM daily_metrics)
        ORDER BY d.popularity DESC
        LIMIT 10
    """)
    save_to_processed(top10, 'movies_top10_today.csv')

    # 2. Biggest gainers — popularity change over last 7 days
    gainers = run_query("""
        WITH latest AS (
            SELECT id, popularity
            FROM daily_metrics
            WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM daily_metrics)
        ),
        week_ago AS (
            SELECT id, popularity
            FROM daily_metrics
            WHERE snapshot_date = (
                SELECT MIN(snapshot_date) FROM (
                    SELECT DISTINCT snapshot_date FROM daily_metrics
                    ORDER BY snapshot_date DESC
                    LIMIT 7
                )
            )
        )
        SELECT m.title, m.release_year,
               CONCAT(m.title, ' (', CAST(m.release_year AS VARCHAR), ')') as display_title,
               l.popularity as popularity_today,
               w.popularity as popularity_7d_ago,
               ROUND(l.popularity - w.popularity, 2) as popularity_change,
               ROUND(((l.popularity - w.popularity) / NULLIF(w.popularity, 0)) * 100, 1) as pct_change
        FROM latest l
        JOIN week_ago w ON l.id = w.id
        JOIN movies_master m ON l.id = m.id
        WHERE l.popularity > w.popularity
        ORDER BY popularity_change DESC
        LIMIT 15
    """)
    save_to_processed(gainers, 'movies_gainers_7d.csv')

    # 3. Biggest losers — popularity drop over last 7 days
    losers = run_query("""
        WITH latest AS (
            SELECT id, popularity
            FROM daily_metrics
            WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM daily_metrics)
        ),
        week_ago AS (
            SELECT id, popularity
            FROM daily_metrics
            WHERE snapshot_date = (
                SELECT MIN(snapshot_date) FROM (
                    SELECT DISTINCT snapshot_date FROM daily_metrics
                    ORDER BY snapshot_date DESC
                    LIMIT 7
                )
            )
        )
        SELECT m.title, m.release_year,
               CONCAT(m.title, ' (', CAST(m.release_year AS VARCHAR), ')') as display_title,
               l.popularity as popularity_today,
               w.popularity as popularity_7d_ago,
               ROUND(w.popularity - l.popularity, 2) as popularity_drop,
               ROUND(((w.popularity - l.popularity) / NULLIF(w.popularity, 0)) * 100, 1) as pct_drop
        FROM latest l
        JOIN week_ago w ON l.id = w.id
        JOIN movies_master m ON l.id = m.id
        WHERE w.popularity > l.popularity
        AND w.popularity > 10
        ORDER BY popularity_drop DESC
        LIMIT 15
    """)
    save_to_processed(losers, 'movies_losers_7d.csv')

    # 4. Average popularity by release year (today)
    by_year = run_query("""
        SELECT m.release_year,
               ROUND(AVG(d.popularity), 2) as avg_popularity,
               COUNT(DISTINCT d.id) as movie_count
        FROM daily_metrics d
        JOIN movies_master m ON d.id = m.id
        WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM daily_metrics)
        GROUP BY m.release_year
        ORDER BY m.release_year
    """)
    save_to_processed(by_year, 'movies_by_year.csv')

    # 5. Average rating by genre (today)
    genre_data = run_query("""
        SELECT m.genre_ids,
               ROUND(AVG(d.vote_average), 2) as avg_rating,
               COUNT(DISTINCT d.id) as movie_count
        FROM daily_metrics d
        JOIN movies_master m ON d.id = m.id
        WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM daily_metrics)
        AND m.genre_ids IS NOT NULL
        GROUP BY m.genre_ids
    """)
    save_to_processed(genre_data, 'movies_genre_ratings.csv')

    # 6. Language distribution
    lang_data = run_query("""
        SELECT m.original_language, COUNT(DISTINCT m.id) as movie_count
        FROM movies_master m
        GROUP BY m.original_language
        ORDER BY movie_count DESC
        LIMIT 12
    """)
    save_to_processed(lang_data, 'movies_language_dist.csv')

    # 7. Top 10 most voted (today)
    top_voted = run_query("""
        SELECT m.title, m.release_year, d.vote_count, d.vote_average,
               CONCAT(m.title, ' (', CAST(m.release_year AS VARCHAR), ')') as display_title
        FROM daily_metrics d
        JOIN movies_master m ON d.id = m.id
        WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM daily_metrics)
        ORDER BY d.vote_count DESC
        LIMIT 10
    """)
    save_to_processed(top_voted, 'movies_top_voted.csv')

    print('Movies done.')


# ── TV Shows aggregations ─────────────────────────────────────────────────────

def process_tv():
    print('Processing TV shows...')

    # 1. Top 10 most popular today
    top10 = run_query("""
        SELECT t.name, t.first_air_year, d.popularity, d.vote_average, d.vote_count,
               CONCAT(t.name, ' (', CAST(t.first_air_year AS VARCHAR), ')') as display_title
        FROM tv_daily_metrics d
        JOIN tv_master t ON d.id = t.id
        WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM tv_daily_metrics)
        ORDER BY d.popularity DESC
        LIMIT 10
    """)
    save_to_processed(top10, 'tv_top10_today.csv')

    # 2. Biggest gainers — last 7 days
    gainers = run_query("""
        WITH latest AS (
            SELECT id, popularity
            FROM tv_daily_metrics
            WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM tv_daily_metrics)
        ),
        week_ago AS (
            SELECT id, popularity
            FROM tv_daily_metrics
            WHERE snapshot_date = (
                SELECT MIN(snapshot_date) FROM (
                    SELECT DISTINCT snapshot_date FROM tv_daily_metrics
                    ORDER BY snapshot_date DESC
                    LIMIT 7
                )
            )
        )
        SELECT t.name, t.first_air_year,
               CONCAT(t.name, ' (', CAST(t.first_air_year AS VARCHAR), ')') as display_title,
               l.popularity as popularity_today,
               w.popularity as popularity_7d_ago,
               ROUND(l.popularity - w.popularity, 2) as popularity_change,
               ROUND(((l.popularity - w.popularity) / NULLIF(w.popularity, 0)) * 100, 1) as pct_change
        FROM latest l
        JOIN week_ago w ON l.id = w.id
        JOIN tv_master t ON l.id = t.id
        WHERE l.popularity > w.popularity
        ORDER BY popularity_change DESC
        LIMIT 15
    """)
    save_to_processed(gainers, 'tv_gainers_7d.csv')

    # 3. Biggest losers — last 7 days
    losers = run_query("""
        WITH latest AS (
            SELECT id, popularity
            FROM tv_daily_metrics
            WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM tv_daily_metrics)
        ),
        week_ago AS (
            SELECT id, popularity
            FROM tv_daily_metrics
            WHERE snapshot_date = (
                SELECT MIN(snapshot_date) FROM (
                    SELECT DISTINCT snapshot_date FROM tv_daily_metrics
                    ORDER BY snapshot_date DESC
                    LIMIT 7
                )
            )
        )
        SELECT t.name, t.first_air_year,
               CONCAT(t.name, ' (', CAST(t.first_air_year AS VARCHAR), ')') as display_title,
               l.popularity as popularity_today,
               w.popularity as popularity_7d_ago,
               ROUND(w.popularity - l.popularity, 2) as popularity_drop,
               ROUND(((w.popularity - l.popularity) / NULLIF(w.popularity, 0)) * 100, 1) as pct_drop
        FROM latest l
        JOIN week_ago w ON l.id = w.id
        JOIN tv_master t ON l.id = t.id
        WHERE w.popularity > l.popularity
        AND w.popularity > 10
        ORDER BY popularity_drop DESC
        LIMIT 15
    """)
    save_to_processed(losers, 'tv_losers_7d.csv')

    # 4. Average popularity by first air year
    by_year = run_query("""
        SELECT t.first_air_year,
               ROUND(AVG(d.popularity), 2) as avg_popularity,
               COUNT(DISTINCT d.id) as show_count
        FROM tv_daily_metrics d
        JOIN tv_master t ON d.id = t.id
        WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM tv_daily_metrics)
        AND t.first_air_year IS NOT NULL
        GROUP BY t.first_air_year
        ORDER BY t.first_air_year
    """)
    save_to_processed(by_year, 'tv_by_year.csv')

    # 5. Average rating by genre
    genre_data = run_query("""
        SELECT t.genre_ids,
               ROUND(AVG(d.vote_average), 2) as avg_rating,
               COUNT(DISTINCT d.id) as show_count
        FROM tv_daily_metrics d
        JOIN tv_master t ON d.id = t.id
        WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM tv_daily_metrics)
        AND t.genre_ids IS NOT NULL
        GROUP BY t.genre_ids
    """)
    save_to_processed(genre_data, 'tv_genre_ratings.csv')

    # 6. Language distribution
    lang_data = run_query("""
        SELECT t.original_language, COUNT(DISTINCT t.id) as show_count
        FROM tv_master t
        GROUP BY t.original_language
        ORDER BY show_count DESC
        LIMIT 12
    """)
    save_to_processed(lang_data, 'tv_language_dist.csv')

    # 7. Top 10 most voted
    top_voted = run_query("""
        SELECT t.name, t.first_air_year, d.vote_count, d.vote_average,
               CONCAT(t.name, ' (', CAST(t.first_air_year AS VARCHAR), ')') as display_title
        FROM tv_daily_metrics d
        JOIN tv_master t ON d.id = t.id
        WHERE d.snapshot_date = (SELECT MAX(snapshot_date) FROM tv_daily_metrics)
        ORDER BY d.vote_count DESC
        LIMIT 10
    """)
    save_to_processed(top_voted, 'tv_top_voted.csv')

    print('TV shows done.')


# ── Lambda handler ────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    print(f'Starting processor Lambda — {date.today().isoformat()}')
    try:
        process_movies()
    except Exception as e:
        print(f'ERROR processing movies: {e}')

    try:
        process_tv()
    except Exception as e:
        print(f'ERROR processing TV: {e}')

    print('Processor complete.')
    return {'statusCode': 200, 'body': 'Processed successfully'}


if __name__ == '__main__':
    lambda_handler(None, None)