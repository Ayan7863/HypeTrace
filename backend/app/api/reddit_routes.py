from fastapi import APIRouter, Query, HTTPException
from app.services.reddit_service import fetch_hot_posts, fetch_top_posts, search_posts
from app.db.models import upsert_many, find_many, sentiment_stats

router = APIRouter(prefix="/api/v1/reddit", tags=["Reddit"])

COLLECTION = "reddit_posts"


@router.get("/trends")
async def reddit_trends(
    limit: int = Query(30, le=100),
    subreddit: str = Query("all"),
    time_filter: str = Query("day", enum=["hour", "day", "week", "month", "year"]),
    refresh: bool = Query(False),
):
    """Fetch hot + top Reddit posts with AI enrichment."""
    if refresh:
        posts = await fetch_hot_posts(limit)
        top = await fetch_top_posts(subreddit, time_filter, limit // 2)
        all_posts = {p["post_id"]: p for p in posts + top}.values()
        posts = list(all_posts)[:limit]
        await upsert_many(COLLECTION, posts)
    else:
        posts = await find_many(COLLECTION, limit=limit)
        if not posts:
            posts = await fetch_hot_posts(limit)
            await upsert_many(COLLECTION, posts)

    return {
        "total": len(posts),
        "source": "reddit",
        "posts": [{k: v for k, v in p.items() if k != "embedding"} for p in posts],
    }


@router.get("/search")
async def reddit_search(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, le=50),
):
    """Search Reddit posts by keyword with AI analysis."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    posts = await search_posts(query.strip(), limit)
    await upsert_many(COLLECTION, posts)
    return {
        "query": query,
        "total": len(posts),
        "posts": [{k: v for k, v in p.items() if k != "embedding"} for p in posts],
    }


@router.get("/sentiment")
async def reddit_sentiment():
    """Sentiment distribution of stored Reddit posts."""
    stats = await sentiment_stats(COLLECTION)
    total = sum(stats.values())
    return {
        "collection": COLLECTION,
        "total_analyzed": total,
        "distribution": stats,
        "percentages": {
            k: round(v / total * 100, 1) if total else 0
            for k, v in stats.items()
        },
    }


@router.get("/posts")
async def reddit_posts(
    limit: int = Query(50, le=200),
    subreddit: str = Query(None),
    sentiment: str = Query(None, enum=["positive", "negative", "neutral"]),
):
    """List stored Reddit posts with optional filters."""
    query: dict = {}
    if subreddit:
        query["subreddit"] = subreddit
    if sentiment:
        query["sentiment"] = sentiment
    posts = await find_many(COLLECTION, query=query, limit=limit)
    return {"total": len(posts), "posts": posts}
