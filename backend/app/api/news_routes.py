from fastapi import APIRouter, Query, HTTPException
from app.services.news_service import fetch_trending_news, fetch_top_headlines, search_news, _has_key
from app.db.models import upsert_many, find_many, sentiment_stats

router = APIRouter(prefix="/api/v1/news", tags=["News"])

COLLECTION = "news_posts"


@router.get("/trends")
async def news_trends(
    limit: int = Query(30, le=100),
    refresh: bool = Query(False),
):
    """Fetch trending news articles with AI enrichment."""
    if not _has_key():
        return {
            "total": 0,
            "source": "news",
            "posts": [],
            "message": "NewsAPI key not configured. Get a free key at https://newsapi.org/register and add NEWS_API_KEY to .env",
        }

    if refresh:
        posts = await fetch_trending_news(limit)
        await upsert_many(COLLECTION, posts)
    else:
        posts = await find_many(COLLECTION, limit=limit)
        if not posts:
            posts = await fetch_trending_news(limit)
            await upsert_many(COLLECTION, posts)

    return {
        "total": len(posts),
        "source": "news",
        "posts": [{k: v for k, v in p.items() if k != "embedding"} for p in posts],
    }


@router.get("/headlines")
async def top_headlines(limit: int = Query(20, le=100)):
    """Fetch top headlines worldwide."""
    if not _has_key():
        raise HTTPException(status_code=503, detail="NEWS_API_KEY not configured")
    posts = await fetch_top_headlines(limit)
    await upsert_many(COLLECTION, posts)
    return {
        "total": len(posts),
        "posts": [{k: v for k, v in p.items() if k != "embedding"} for p in posts],
    }


@router.get("/search")
async def news_search(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
):
    """Search news articles by keyword."""
    if not _has_key():
        raise HTTPException(status_code=503, detail="NEWS_API_KEY not configured")
    posts = await search_news(query.strip(), limit)
    await upsert_many(COLLECTION, posts)
    return {
        "query": query,
        "total": len(posts),
        "posts": [{k: v for k, v in p.items() if k != "embedding"} for p in posts],
    }


@router.get("/sentiment")
async def news_sentiment():
    """Sentiment distribution of stored news articles."""
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
