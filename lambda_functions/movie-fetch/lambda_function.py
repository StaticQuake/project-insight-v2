import requests
import boto3
import pandas as pd
import os
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
import io

API_KEY = os.environ['TMDB_API_KEY']
BUCKET_NAME = os.environ['BUCKET']
MOVIE_IDS_KEY = 'raw/movie_ids.csv'

s3 = boto3.client('s3')

#moviesss
s3 = boto3.client('s3', region_name='us-east-1')
athena = boto3.client('athena', region_name='us-east-1')

def get_movie_ids():
    response = s3.get_object(Bucket=BUCKET, Key=MOVIE_IDS_KEY)
    df = pd.read_csv(io.BytesIO(response['Body'].read()))
    return df['id'].tolist()

def fetch_movie(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    try:
        r = requests.get(url, params={"api_key": API_KEY}, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {
                "id": d["id"],
                "popularity": d["popularity"],
                "vote_average": d["vote_average"],
                "vote_count": d["vote_count"]
            }
    except:
        return None

def lambda_handler(event, context):
    print("Starting daily fetch...")

    movie_ids = get_movie_ids()
    print(f"Loaded {len(movie_ids)} movie IDs from S3")

    results, failed = [], []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_movie, mid): mid for mid in movie_ids}
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result:
                results.append(result)
            else:
                failed.append(futures[future])
            if i % 1000 == 0:
                print(f"Progress: {i}/{len(movie_ids)}")

    df = pd.DataFrame(results)

    today = date.today().isoformat()
    s3_key = f"raw/daily_metrics/snapshot_date={today}/metrics_{today}.csv"

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=csv_buffer.getvalue()
    )

    print(f"Done. Success: {len(results)}, Failed: {len(failed)}")
    print(f"Saved to s3://{BUCKET_NAME}/{s3_key}")

    # Register new partition in Athena
    athena.start_query_execution(
        QueryString=f"ALTER TABLE daily_metrics ADD IF NOT EXISTS PARTITION (snapshot_date='{today}') LOCATION 's3://{BUCKET_NAME}/raw/daily_metrics/snapshot_date={today}/'",
        QueryExecutionContext={'Database': 'project_insights'},
        ResultConfiguration={'OutputLocation': f's3://{BUCKET_NAME}/athena-results/'}
    )
    print(f"Partition registered for {today}")

    return {
        "statusCode": 200,
        "body": f"Success: {len(results)}, Failed: {len(failed)}"
    }