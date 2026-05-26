from fastapi import APIRouter, Query
from app.services.twitter_service import fetch_trending_tweets, search_tweets
from app.db.models import upsert_many, find_many, sentiment_stats

router = APIRouter(prefix="/api/v1/twitter", tags=["Twitter/X"])

COLLECTION = "twitter_posts"


@router.get("/trends")
async def twitter_trends(
    limit: int = Query(30, le=100),
    refresh: bool = Query(False),
):
    if refresh:
        posts = await fetch_trending_tweets(limit)
        await upsert_many(COLLECTION, posts)
    else:
        posts = await find_many(COLLECTION, limit=limit)
        if not posts:
            posts = await fetch_trending_tweets(limit)
            await upsert_many(COLLECTION, posts)
    return {
        "total": len(posts),
        "source": "twitter",
        "posts": [{k: v for k, v in p.items() if k != "embedding"} for p in posts],
    }


@router.get("/search")
async def twitter_search(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
):
    posts = await search_tweets(query.strip(), limit)
    await upsert_many(COLLECTION, posts)
    return {
        "query": query,
        "total": len(posts),
        "posts": [{k: v for k, v in p.items() if k != "embedding"} for p in posts],
    }


@router.get("/sentiment")
async def twitter_sentiment():
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
async def twitter_posts(
    limit: int = Query(50, le=200),
    sentiment: str = Query(None, enum=["positive", "negative", "neutral"]),
):
    query: dict = {}
    if sentiment:
        query["sentiment"] = sentiment
    posts = await find_many(COLLECTION, query=query, limit=limit)
    return {"total": len(posts), "posts": posts}
