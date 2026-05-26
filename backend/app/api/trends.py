from fastapi import APIRouter, Query, HTTPException, Request
from app.schemas.trend import FetchRequest, AnalyzeRequest
from app.services import trend_service, ai_service
from app.services.mock_service import generate_mock_posts
from app.core.config import get_settings
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/trends", tags=["trends"])
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


async def _fetch_from_source(source: str, limit: int) -> list[dict]:
    source_lower = source.lower().strip()
    
    if source_lower == "reddit":
        from app.services.reddit_service import fetch_hot_posts
        return await fetch_hot_posts(limit)

    if source_lower in ("x", "twitter"):
        from app.services.twitter_service import fetch_trending_tweets
        return await fetch_trending_tweets(limit)

    if source_lower in ("yt", "youtube"):
        from app.services.youtube_service import fetch_youtube_posts
        return fetch_youtube_posts(limit)

    if source_lower in ("insta", "instagram"):
        from app.services.instagram_service import fetch_trending_instagram
        return await fetch_trending_instagram(limit)

    if source_lower == "news":
        from app.services.news_service import fetch_trending_news
        return await fetch_trending_news(limit)

    return []


@router.post("/fetch")
@limiter.limit("10/minute")
async def fetch_trends(request: Request, body: FetchRequest):
    posts = []

    # Map standardized source names
    standard_sources = []
    for s in body.sources:
        s_lower = s.lower().strip()
        if s_lower in ("x", "twitter"):
            standard_sources.append("twitter")
        elif s_lower in ("insta", "instagram"):
            standard_sources.append("instagram")
        elif s_lower in ("yt", "youtube"):
            standard_sources.append("youtube")
        elif s_lower == "news":
            standard_sources.append("news")
        else:
            standard_sources.append("reddit")

    for source in standard_sources:
        try:
            fetched = await _fetch_from_source(source, body.limit)
            posts.extend(fetched)
        except Exception as e:
            import logging
            logging.error(f"Error fetching from {source}: {e}")
            continue

    # Fall back to mock data if no real API keys are configured
    if not posts:
        posts = generate_mock_posts(body.limit)
        mode = "mock"
    else:
        mode = "live"

    result = await trend_service.upsert_posts(posts)
    inserted = result.get("inserted", 0)
    updated = result.get("updated", 0)
    return {
        "fetched": len(posts),
        "inserted": inserted,
        "updated": updated,
        "sources": standard_sources,
        "mode": mode,
    }


@router.post("/analyze")
@limiter.limit("5/minute")
async def analyze_trends(request: Request, body: AnalyzeRequest):
    from app.core.database import get_db
    db = get_db()
    col = db["posts"]

    query = {} if body.recompute else {"sentiment_label": None}
    cursor = col.find(query, {"embedding": 0, "embedding_vector": 0})
    posts = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        posts.append(doc)

    if not posts:
        return {"analyzed": 0, "message": "No posts to analyze"}

    analyzed = ai_service.run_full_analysis(posts)
    
    # Save back to database
    for post in analyzed:
        post_copy = post.copy()
        post_copy.pop("_id", None)
        await col.update_one({"post_id": post["post_id"]}, {"$set": post_copy})
        
    return {"analyzed": len(analyzed)}


@router.get("/")
async def list_trends(
    source: str = Query(None),
    limit: int = Query(50, le=200),
):
    posts = await trend_service.get_all_posts(limit=limit, source=source)
    return {"posts": posts, "total": len(posts)}


@router.get("/topics")
async def list_topics():
    topics = await trend_service.get_topic_summaries()
    return {"topics": topics}


@router.get("/stats/sentiment")
async def sentiment_stats():
    return await trend_service.get_sentiment_stats()


@router.get("/stats/sources")
async def source_stats():
    return await trend_service.get_source_stats()
