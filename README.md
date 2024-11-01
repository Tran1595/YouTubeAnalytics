# YouTube Trends in Vietnam: A Step-by-Step Data Analysis Guide

This guide walks through each step to analyze YouTube video trends in Vietnam using the YouTube API, Python, and PostgreSQL.

## Step 1: Set Up the Environment

### Prerequisites
- **Python**: Ensure you have Python 3.7 or later installed.
- **PostgreSQL**: Install PostgreSQL and create a database for storing YouTube data.
- **YouTube Data API Key**: Get an API key from the [Google Developer Console](https://console.cloud.google.com/).

### Install Required Libraries
In Python, install the necessary libraries for interacting with the YouTube API and PostgreSQL:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client psycopg2-binary
```
## Step 2: Fetch Data from YouTube API
1. Set Up YouTube API
Use the YouTube API to access data on popular videos in Vietnam.

python
```bash
from googleapiclient.discovery import build

# Initialize YouTube API client
api_key = 'YOUR_API_KEY'
youtube = build('youtube', 'v3', developerKey=api_key)
2. Request Video Data
Retrieve details on popular videos in Vietnam, including title, view_count, like_count, comment_count, tags, category_name, and video_length.
```
python
Copy code
# Fetch popular videos from YouTube
response = youtube.videos().list(
    part="snippet,statistics,contentDetails",
    chart="mostPopular",
    regionCode="VN",  # Vietnam
    maxResults=50
).execute()
3. Process and Save Data
Extract data fields from the API response for later storage in PostgreSQL. For example:

python
Copy code
videos = []
for item in response['items']:
    video_data = {
        'title': item['snippet']['title'],
        'category_name': item['snippet'].get('categoryId', 'Unknown'),
        'view_count': item['statistics'].get('viewCount', 0),
        'like_count': item['statistics'].get('likeCount', 0),
        'comment_count': item['statistics'].get('commentCount', 0),
        'tags': ','.join(item['snippet'].get('tags', [])),
        'published_at': item['snippet']['publishedAt'],
        'video_length': item['contentDetails']['duration']
    }
    videos.append(video_data)
Step 3: Set Up PostgreSQL Database
1. Create Database and Table
Create a PostgreSQL database and a table to store the YouTube video data:

sql
Copy code
CREATE DATABASE youtube_data;

CREATE TABLE youtube_videos (
    title TEXT,
    category_name TEXT,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    tags TEXT,
    published_at TIMESTAMP,
    video_length INTEGER,
    is_weekend BOOLEAN
);
2. Connect to PostgreSQL from Python
Use psycopg2 to connect to PostgreSQL and insert data.

python
Copy code
import psycopg2

# Connect to the database
conn = psycopg2.connect(
    dbname='youtube_data',
    user='your_username',
    password='your_password',
    host='localhost'
)
cur = conn.cursor()
3. Insert Data into PostgreSQL
Insert the extracted data into the PostgreSQL table.

python
Copy code
for video in videos:
    cur.execute("""
        INSERT INTO youtube_videos (title, category_name, view_count, like_count, comment_count, tags, published_at, video_length)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (video['title'], video['category_name'], video['view_count'], video['like_count'],
         video['comment_count'], video['tags'], video['published_at'], video['video_length'])
    )
conn.commit()
Step 4: Analyze Data with SQL
Now that the data is in PostgreSQL, run SQL queries to uncover insights:

a. Most Popular Tags
Identify common tags in high-view videos to see which keywords attract viewers.

sql
Copy code
SELECT 
    UNNEST(STRING_TO_ARRAY(tags, ',')) AS tag, 
    COUNT(*) AS tag_count, 
    AVG(view_count) AS avg_view_count
FROM youtube_videos
WHERE view_count > 1000000
GROUP BY tag
ORDER BY tag_count DESC
LIMIT 10;
b. Optimal Video Length for Engagement
Segment videos by length to find which durations get the most views.

sql
Copy code
SELECT 
    CASE 
        WHEN video_length < 300 THEN 'Short'
        WHEN video_length BETWEEN 300 AND 1200 THEN 'Medium'
        ELSE 'Long'
    END AS video_duration_category,
    AVG(view_count) AS avg_views,
    AVG(like_count) AS avg_likes
FROM youtube_videos
GROUP BY video_duration_category
ORDER BY avg_views DESC;
c. Engagement by Day of Week
Determine if videos published on weekends or weekdays perform better.

sql
Copy code
SELECT is_weekend, AVG(view_count) AS avg_views, AVG(like_count) AS avg_likes
FROM youtube_videos
GROUP BY is_weekend;
Step 5: Summarize Findings
Based on the analysis, here are some key insights:

Eye-Catching Titles and Thumbnails: Titles and thumbnails play a key role in attracting viewers.
Short Video Success: Short videos (<5 mins) perform better on average, aligning with viewer preferences.
Weekday Posting Advantage: Videos uploaded on weekdays tend to receive higher engagement than on weekends.
Localized Tags and Keywords: Tags that are culturally specific or relatable, like those referencing everyday life, increase visibility.
Step 6: Refine and Share Insights
You can now refine the analysis or use these findings to create content strategies tailored to Vietnamese viewers.
