from fastapi import APIRouter, Query
from app.db.models import find_many
from sklearn.preprocessing import MinMaxScaler
import numpy as np

router = APIRouter(prefix="/api/v1/trends", tags=["Unified Trends"])


def _normalize_scores(posts: list[dict]) -> list[dict]:
    if len(posts) < 2:
        return posts
    scores = np.array([[p.get("trend_score", 0)] for p in posts], dtype=float)
    if scores.max() == scores.min():
        for p in posts:
            p["trend_score_normalized"] = 50.0
        return posts
    scaler = MinMaxScaler(feature_range=(0, 100))
    normalized = scaler.fit_transform(scores).flatten()
    for i, p in enumerate(posts):
        p["trend_score_normalized"] = round(float(normalized[i]), 2)
    return posts


@router.get("/all")
async def all_trends(
    limit: int = Query(60, le=200),
    source: str = Query(None, enum=["reddit", "twitter", "youtube", "instagram"]),
    sentiment: str = Query(None, enum=["positive", "negative", "neutral"]),
    min_score: float = Query(None),
):
    query: dict = {}
    if sentiment:
        query["sentiment_label"] = sentiment
    if source:
        query["platform"] = source

    all_posts = await find_many("posts", query=query, limit=limit, sort_by="trend_score")

    from app.services.ai_service import compute_trend_score_for_batch
    all_posts = compute_trend_score_for_batch(all_posts)
    all_posts.sort(key=lambda x: x.get("trend_score", 0.0), reverse=True)

    if min_score is not None:
        all_posts = [p for p in all_posts if p.get("trend_score", 0) >= min_score]

    all_posts = _normalize_scores(all_posts)

    source_counts: dict = {}
    for p in all_posts:
        s = p.get("platform", "unknown")
        source_counts[s] = source_counts.get(s, 0) + 1

    return {
        "total": len(all_posts),
        "source_breakdown": source_counts,
        "posts": all_posts,
    }


@router.get("/stats")
async def trend_stats():
    """Aggregated stats from the unified posts collection."""
    from app.core.database import get_db
    db = get_db()

    stats: dict = {}
    for platform in ["reddit", "twitter", "youtube", "instagram"]:
        posts = await find_many("posts", query={"platform": platform}, limit=1000, sort_by="trend_score")
        if posts:
            scores = [p.get("trend_score", 0) for p in posts if p.get("trend_score")]
            sentiments = [p.get("sentiment_label") for p in posts]
            stats[platform] = {
                "total_posts": len(posts),
                "avg_trend_score": round(sum(scores) / len(scores), 2) if scores else 0,
                "top_trend_score": round(max(scores), 2) if scores else 0,
                "sentiment_breakdown": {
                    "positive": sentiments.count("positive"),
                    "negative": sentiments.count("negative"),
                    "neutral": sentiments.count("neutral"),
                },
            }
        else:
            stats[platform] = {"total_posts": 0}
    return stats
