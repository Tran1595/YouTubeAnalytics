import psycopg2
import googleapiclient.discovery
import isodate
from datetime import datetime
from datetime import timedelta

# YouTube API credentials
DEVELOPER_KEY = "YOUR_API_KEY"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
regionCode = "VN" # Adjusting region
maxResults = 50  # Adjusting to smaller pages for pagination
total_videos = 200  # Total number of videos you want

# PostgreSQL credentials
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "your_password"
DB_HOST = "localhost"
DB_PORT = "5432"

# Connect to PostgreSQL database
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
except psycopg2.Error as e:
    print(f"Database connection error: {e}")

# Get YouTube data
try:
    youtube = googleapiclient.discovery.build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=DEVELOPER_KEY
    )
except Exception as e:
    print(f"Error creating YouTube client: {e}")

# Fetch video categories
try:
    categories_request = youtube.videoCategories().list(
        part="snippet",
        regionCode=regionCode
    )
    categories_response = categories_request.execute()
    category_dict = {cat['id']: cat['snippet']['title'] for cat in categories_response['items']}
except Exception as e:
    print(f"Error fetching video categories: {e}")

def fetch_and_store_videos(page_token=None, videos_fetched=0):
    print(f"Fetching with page_token: {page_token}, videos_fetched: {videos_fetched}")
    if videos_fetched >= total_videos:
        return
    try:
        request = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            chart="mostPopular",
            regionCode=regionCode,
            maxResults=maxResults,
            pageToken=page_token
        )
        response = request.execute()
    except Exception as e:
        print(f"Error fetching YouTube data: {e}")
        return
    for item in response['items']:
        if videos_fetched >= total_videos:
            break
        title = item['snippet']['title']
        category_name = category_dict.get(item['snippet']['categoryId'], "Unknown")
        view_count = item['statistics'].get('viewCount', 0)
        like_count = item['statistics'].get('likeCount', 0)
        comment_count = item['statistics'].get('commentCount', 0)
        published_at = item['snippet']['publishedAt']
        video_length = isodate.parse_duration(item['contentDetails']['duration']).total_seconds()
        # Convert to HH:MM:SS format
        video_duration = str(timedelta(seconds=video_length))
        print(video_duration)  # Outputs: formatted time like '2:08:11'
        thumbnail_url = item['snippet']['thumbnails']['high']['url']
        tags = ','.join(item['snippet'].get('tags', []))
        published_datetime = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
        is_weekend = published_datetime.weekday() >= 5
        channel_id = item['snippet']['channelId']
        try:
            channel_request = youtube.channels().list(
                part="statistics",
                id=channel_id
            )
            channel_response = channel_request.execute()
            channel_info = channel_response['items'][0]['statistics']
            subscriber_count = channel_info.get('subscriberCount', 0)
            video_count = channel_info.get('videoCount', 0)
        except Exception as e:
            print(f"Error fetching channel data: {e}")
            subscriber_count = 0
            video_count = 0
        try:
            cursor.execute('''
                            INSERT INTO youtube_videos (title, category_name, view_count, like_count, comment_count,
                             published_at, thumbnail_url, tags, subscriber_count, video_count, is_weekend,video_length)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (
                title, category_name, view_count, like_count, comment_count, published_at,
                thumbnail_url,
                tags, subscriber_count, video_count, is_weekend,video_duration
            ))
            conn.commit()  # Commit the transaction
            videos_fetched += 1
            print(f"Fetched and stored video #{videos_fetched}")
        except psycopg2.Error as e:
            print(f"Database insertion error: {e}")
    next_page_token = response.get('nextPageToken')
    print(f"Next Page Token: {next_page_token}")
    if next_page_token and videos_fetched < total_videos:
        fetch_and_store_videos(next_page_token, videos_fetched)

# Start fetching and storing videos
fetch_and_store_videos()

# Close the cursor and connection
cursor.close()
conn.close()
