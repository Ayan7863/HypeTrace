from fastapi import APIRouter, Query
from app.services.instagram_service import fetch_trending_instagram, search_instagram
from app.db.models import upsert_many, find_many, sentiment_stats

router = APIRouter(prefix="/api/v1/instagram", tags=["Instagram"])

COLLECTION = "instagram_posts"


@router.get("/trends")
async def instagram_trends(
    limit: int = Query(30, le=100),
    refresh: bool = Query(False),
):
    if refresh:
        posts = await fetch_trending_instagram(limit)
        await upsert_many(COLLECTION, posts)
    else:
        posts = await find_many(COLLECTION, limit=limit)
        if not posts:
            posts = await fetch_trending_instagram(limit)
            await upsert_many(COLLECTION, posts)
    return {
        "total": len(posts),
        "source": "instagram",
        "posts": [{k: v for k, v in p.items() if k != "embedding"} for p in posts],
    }


@router.get("/search")
async def instagram_search(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
):
    posts = await search_instagram(query.strip(), limit)
    await upsert_many(COLLECTION, posts)
    return {
        "query": query,
        "total": len(posts),
        "posts": [{k: v for k, v in p.items() if k != "embedding"} for p in posts],
    }


@router.get("/sentiment")
async def instagram_sentiment():
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
async def instagram_posts(
    limit: int = Query(50, le=200),
    sentiment: str = Query(None, enum=["positive", "negative", "neutral"]),
):
    query: dict = {}
    if sentiment:
        query["sentiment"] = sentiment
    posts = await find_many(COLLECTION, query=query, limit=limit)
    return {"total": len(posts), "posts": posts}
