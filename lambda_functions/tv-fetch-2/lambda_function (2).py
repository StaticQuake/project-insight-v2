import requests
import boto3
import pandas as pd
import os
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
import io

API_KEY = os.environ['TMDB_API_KEY']
BUCKET_NAME = os.environ['BUCKET']
TV_IDS_KEY = 'raw/tv_ids_part2.csv'

s3 = boto3.client('s3')
athena = boto3.client('athena')
#tv 2
def get_tv_ids():
    response = s3.get_object(Bucket=BUCKET_NAME, Key=TV_IDS_KEY)
    df = pd.read_csv(io.BytesIO(response['Body'].read()))
    return df['id'].tolist()


def fetch_tv_show(tv_id):
    url = f'https://api.themoviedb.org/3/tv/{tv_id}'
    try:
        r = requests.get(url, params={'api_key': API_KEY}, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {
                'id': d['id'],
                'popularity': d['popularity'],
                'vote_average': d['vote_average'],
                'vote_count': d['vote_count']
            }
    except:
        return None


def lambda_handler(event, context):
    print('Starting TV daily fetch - Part 2...')

    tv_ids = get_tv_ids()
    print(f'Loaded {len(tv_ids)} TV show IDs from S3 (Part 2)')

    results, failed = [], []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_tv_show, tid): tid for tid in tv_ids}
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result:
                results.append(result)
            else:
                failed.append(futures[future])
            if i % 1000 == 0:
                print(f'Progress: {i}/{len(tv_ids)}')

    df = pd.DataFrame(results)
    today = date.today().isoformat()

    # Part 2 saves metrics_part2_YYYY-MM-DD.csv
    s3_key = f'raw/tv_daily_metrics/snapshot_date={today}/metrics_part2_{today}.csv'
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    s3.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=csv_buffer.getvalue())
    print(f'Saved {len(results)} rows to {s3_key}')

    print(f'Part 2 done. Success: {len(results)}, Failed: {len(failed)}')

    # Part 2 registers the Athena partition for today
    athena.start_query_execution(
        QueryString=f"ALTER TABLE tv_daily_metrics ADD IF NOT EXISTS PARTITION (snapshot_date='{today}') LOCATION 's3://{BUCKET_NAME}/raw/tv_daily_metrics/snapshot_date={today}/'",
        QueryExecutionContext={'Database': 'project_insights'},
        ResultConfiguration={'OutputLocation': f's3://{BUCKET_NAME}/athena-results/'}
    )
    print(f'Partition registered for {today}')

    return {'statusCode': 200, 'body': f'Part 2 - Success: {len(results)}, Failed: {len(failed)}'}