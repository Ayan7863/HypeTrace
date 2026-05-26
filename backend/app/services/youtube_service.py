from googleapiclient.discovery import build
from app.core.config import get_settings
from datetime import datetime

settings = get_settings()

YOUTUBE_CATEGORIES = ["28", "10", "20", "24", "25"]  # Tech, Music, Gaming, News, News


def get_youtube_client():
    return build("youtube", "v3", developerKey=settings.youtube_api_key)


def fetch_youtube_posts(limit: int = 20) -> list[dict]:
    youtube = get_youtube_client()
    posts = []

    try:
        response = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode="US",
            maxResults=min(limit, 50),
        ).execute()

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            
            # Map to Unified Schema
            posts.append({
                "platform": "youtube",
                "source": "youtube",
                "post_id": f"youtube_{item['id']}",
                "title": snippet.get("title", ""),
                "content": snippet.get("description", "")[:600],
                "author": snippet.get("channelTitle", "unknown"),
                "url": f"https://youtube.com/watch?v={item['id']}",
                "engagement": {
                    "likes": likes,
                    "comments": comments,
                    "shares": 0
                },
                "likes": likes,
                "comments_count": comments,
                "score": float(stats.get("viewCount", 0)),
                "timestamp": datetime.utcnow(),
                "fetched_at": datetime.utcnow(),
            })
    except Exception:
        pass

    enriched_posts = posts[:limit]
    if enriched_posts:
        from app.services.ai_service import run_full_analysis
        try:
            enriched_posts = run_full_analysis(enriched_posts)
        except Exception:
            pass
            
    return enriched_posts
