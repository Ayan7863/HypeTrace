from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.core.database import get_db
from app.services.ai_service import compute_trend_score_for_batch, generate_ai_insights
from datetime import datetime, timedelta
import math
import asyncio
import json

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_eng(n: int) -> str:
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}k"
    return str(n)


def _trend_phase(score: float, momentum: float, hours_old: float) -> str:
    """Classify a post into a lifecycle phase."""
    if score >= 8.0 and momentum >= 0:
        return "Viral"
    if score >= 6.5 and momentum >= 0 and hours_old < 12:
        return "Emerging"
    if momentum < -0.5 or hours_old > 48:
        return "Declining"
    return "Stable"


def _virality_probability(score: float, is_spike: bool, sentiment_score: float, engagement: int) -> float:
    """0–100 probability that this post will go viral in the next 24h."""
    base = (score / 10.0) * 60.0
    if is_spike:
        base += 25.0
    base += abs(sentiment_score) * 10.0
    base += min(math.log1p(engagement) / math.log1p(500_000) * 10.0, 10.0)
    return round(min(base, 99.0), 1)


def _build_decay_series(score: float, hours_old: float, is_spike: bool, n_points: int = 8) -> list[float]:
    """Simulate a realistic engagement curve. t is always >= 0."""
    import random
    points = []
    h = max(hours_old, 0.1)
    for i in range(n_points):
        # t goes from 0 (post creation) to h (now), linearly
        t = h * i / max(n_points - 1, 1)
        if is_spike:
            peak_t = max(h * 0.15, 0.3)
            if t <= peak_t:
                v = score * 0.2 + score * 0.8 * (t / peak_t)
            else:
                v = score * math.exp(-(t - peak_t) / 18.0)
        else:
            peak_t = max(h * 0.3, 1.0)
            if t <= peak_t:
                v = score * 0.35 + score * 0.65 * (t / peak_t)
            else:
                v = score * math.exp(-(t - peak_t) / 30.0)
        noise = random.uniform(-0.12, 0.12)
        points.append(round(max(1.0, min(10.0, float(v) + noise)), 2))
    return points


def _per_trend_summary(post: dict) -> str:
    """Generate a concise AI-style summary for a single trend post."""
    title = post.get("title", "")
    platform = (post.get("platform") or post.get("source") or "social media").capitalize()
    topic = post.get("topic") or post.get("topic_label") or "General"
    sentiment = post.get("sentiment_label") or post.get("sentiment") or "neutral"
    score = post.get("trend_score", 0.0)
    phase = post.get("trend_phase", "Stable")
    eng = post.get("engagement") or {}
    total_eng = (eng.get("likes", 0) or 0) + (eng.get("comments", 0) or 0) + (eng.get("shares", 0) or 0) if isinstance(eng, dict) else 0

    sentiment_desc = {
        "positive": "generating strong positive reception",
        "negative": "sparking controversy and critical discussion",
        "neutral": "attracting informational engagement",
    }.get(sentiment, "generating mixed reactions")

    phase_desc = {
        "Viral": "rapidly accelerating across platforms",
        "Emerging": "gaining early traction with growth potential",
        "Declining": "past peak engagement, tapering off",
        "Stable": "maintaining consistent steady engagement",
    }.get(phase, "showing steady activity")

    return (
        f"This {topic} post is {phase_desc} on {platform}, {sentiment_desc}. "
        f"Trend score {score}/10 with {_fmt_eng(total_eng)} total interactions."
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/search")
async def search_posts(
    q: str = Query(..., min_length=1),
    platform: str = Query(None),
    limit: int = Query(30, le=100),
):
    db = get_db()
    filter_query: dict = {"$or": [
        {"title": {"$regex": q, "$options": "i"}},
        {"content": {"$regex": q, "$options": "i"}},
        {"topic": {"$regex": q, "$options": "i"}},
    ]}
    if platform:
        p = platform.lower().strip()
        filter_query["platform"] = "twitter" if p in ("x", "twitter") else p

    cursor = db.posts.find(filter_query, {"embedding": 0, "embedding_vector": 0}) \
        .sort("trend_score", -1).limit(limit)
    posts = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc.get("post_id")
        doc["source"] = doc.get("platform")
        doc["sentiment"] = doc.get("sentiment_label")
        doc["topic_label"] = doc.get("topic")
        posts.append(doc)
    return {"query": q, "total": len(posts), "posts": posts}


@router.get("/stream")
async def stream_analytics(platform: str = Query(None)):
    """SSE endpoint — pushes a lightweight stats update every 30s."""
    async def event_generator():
        while True:
            try:
                db = get_db()
                fq = {}
                if platform:
                    p = platform.lower().strip()
                    fq["platform"] = "twitter" if p in ("x", "twitter") else p

                total = await db.posts.count_documents(fq)
                spike_count = await db.posts.count_documents({**fq, "is_spike": True})
                max_doc = await db.posts.find(fq).sort("trend_score", -1).limit(1).to_list(1)
                top_score = max_doc[0].get("trend_score", 0.0) if max_doc else 0.0

                payload = json.dumps({
                    "total_posts": total,
                    "spike_count": spike_count,
                    "top_trend_score": round(top_score, 2),
                    "ts": datetime.utcnow().isoformat() + "Z",
                })
                yield f"data: {payload}\n\n"
            except Exception:
                yield f"data: {{}}\n\n"
            await asyncio.sleep(30)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/analytics")
async def get_dashboard_analytics(
    platform: str = Query(None, description="Filter by platform")
):
    db = get_db()
    now = datetime.utcnow()

    # 1. Filter
    filter_query = {}
    if platform:
        p = platform.lower().strip()
        if p in ("x", "twitter"):   filter_query["platform"] = "twitter"
        elif p in ("insta", "instagram"): filter_query["platform"] = "instagram"
        elif p in ("yt", "youtube"): filter_query["platform"] = "youtube"
        else: filter_query["platform"] = p

    # 2. Total posts
    total_posts = await db.posts.count_documents(filter_query)

    # 3. Sentiment — single source of truth from DB
    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    async for doc in db.posts.aggregate([
        {"$match": filter_query},
        {"$group": {"_id": "$sentiment_label", "count": {"$sum": 1}}}
    ]):
        lbl = doc["_id"]
        if lbl in sentiment_distribution:
            sentiment_distribution[lbl] = doc["count"]

    sent_total = sum(sentiment_distribution.values())
    for k in ("positive", "negative", "neutral"):
        sentiment_distribution[f"{k}_pct"] = round(
            sentiment_distribution[k] / sent_total * 100, 1
        ) if sent_total else 0

    # 4. Platform distribution — sorted by count, with engagement
    platform_distribution = []
    async for doc in db.posts.aggregate([
        {"$match": filter_query},
        {"$group": {
            "_id": "$platform",
            "count": {"$sum": 1},
            "avg_trend_score": {"$avg": "$trend_score"},
            "total_likes": {"$sum": "$engagement.likes"},
            "total_comments": {"$sum": "$engagement.comments"},
            "total_shares": {"$sum": "$engagement.shares"},
        }},
        {"$sort": {"count": -1}}
    ]):
        plat = doc["_id"]
        if plat:
            total_eng = (doc.get("total_likes") or 0) + (doc.get("total_comments") or 0) + (doc.get("total_shares") or 0)
            platform_distribution.append({
                "source": plat,
                "count": doc["count"],
                "avg_trend_score": round(doc["avg_trend_score"] or 0.0, 2),
                "trend_score": round(doc["avg_trend_score"] or 0.0, 2),
                "total_engagement": total_eng,
                "percentage": 0.0,
            })

    total_plat = sum(p["count"] for p in platform_distribution)
    for p in platform_distribution:
        p["percentage"] = round(p["count"] / total_plat * 100, 1) if total_plat else 0.0

    all_platforms = ["reddit", "twitter", "youtube", "instagram", "news"]
    existing = {p["source"] for p in platform_distribution}
    for plat in all_platforms:
        if plat not in existing and (not platform or filter_query.get("platform") == plat):
            platform_distribution.append({
                "source": plat, "count": 0, "avg_trend_score": 0.0,
                "trend_score": 0.0, "total_engagement": 0, "percentage": 0.0
            })

    # 5. Fetch & score posts
    cursor = db.posts.find(filter_query).sort("timestamp", -1).limit(200)
    recent_posts = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc.get("post_id")
        doc["source"] = doc.get("platform")
        doc["sentiment"] = doc.get("sentiment_label")
        doc["topic_label"] = doc.get("topic")
        recent_posts.append(doc)

    enriched = compute_trend_score_for_batch(recent_posts)

    # Compute batch average for momentum baseline
    scores = [p.get("trend_score", 0.0) for p in enriched]
    avg_batch_score = sum(scores) / len(scores) if scores else 6.5

    # Annotate each post with phase, virality, and per-trend summary
    for p in enriched:
        ts = p.get("timestamp") or p.get("fetched_at") or now
        if isinstance(ts, str):
            try: ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
            except: ts = now
        elif not isinstance(ts, datetime):
            ts = now
        if hasattr(ts, "tzinfo") and ts.tzinfo:
            ts = ts.replace(tzinfo=None)
        hours_old = max(0.0, (now - ts).total_seconds() / 3600.0)

        score = p.get("trend_score", 0.0)
        # momentum = how much above/below the batch average this post is
        momentum = round(score - avg_batch_score, 2)
        is_spike = p.get("is_spike", False)
        eng = p.get("engagement") or {}
        total_eng = (eng.get("likes", 0) or 0) + (eng.get("comments", 0) or 0) + (eng.get("shares", 0) or 0) if isinstance(eng, dict) else 0
        sent_score = float(p.get("sentiment_score") or 0.0)

        p["trend_phase"] = _trend_phase(score, momentum, hours_old)
        p["virality_score"] = _virality_probability(score, is_spike, sent_score, total_eng)
        p["hours_old"] = round(hours_old, 1)
        p["ai_summary"] = _per_trend_summary(p)

    enriched.sort(key=lambda x: x.get("trend_score", 0.0), reverse=True)
    top_trends = enriched[:60]

    # Sync back to MongoDB
    for p in top_trends:
        try:
            from bson import ObjectId
            await db.posts.update_one(
                {"_id": ObjectId(p["_id"])},
                {"$set": {
                    "trend_score": p["trend_score"],
                    "is_spike": p.get("is_spike", False),
                    "trend_phase": p.get("trend_phase"),
                    "virality_score": p.get("virality_score"),
                }}
            )
        except Exception:
            pass

    # 6. Topic clusters
    topic_clusters = []
    async for doc in db.posts.aggregate([
        {"$match": {**filter_query, "topic": {"$ne": None}}},
        {"$group": {
            "_id": "$topic",
            "post_count": {"$sum": 1},
            "avg_sentiment": {"$avg": "$sentiment_score"},
            "avg_trend_score": {"$avg": "$trend_score"},
            "avg_virality": {"$avg": "$virality_score"},
            "top_sources": {"$addToSet": "$platform"},
            "spike_count": {"$sum": {"$cond": [{"$eq": ["$is_spike", True]}, 1, 0]}},
            "phases": {"$push": "$trend_phase"},
        }},
        {"$sort": {"avg_trend_score": -1}},
        {"$limit": 20}
    ]):
        name = doc["_id"]
        if name:
            avg_ts = round(doc["avg_trend_score"] or 0.0, 2)
            phases = [p for p in (doc.get("phases") or []) if p]
            dominant_phase = max(set(phases), key=phases.count) if phases else "Stable"
            topic_clusters.append({
                "topic_label": name,
                "post_count": doc["post_count"],
                "avg_sentiment": round(doc["avg_sentiment"] or 0.0, 2),
                "avg_trend_score": avg_ts,
                "avg_virality": round(doc.get("avg_virality") or 0.0, 1),
                "top_sources": list(doc["top_sources"]),
                "spike_count": doc.get("spike_count", 0),
                "dominant_phase": dominant_phase,
                "percentage": 0.0,
                "summary": f"'{name}' — {doc['post_count']} posts · {dominant_phase} · avg score {avg_ts}.",
            })

    total_topic_posts = sum(t["post_count"] for t in topic_clusters)
    for t in topic_clusters:
        t["percentage"] = round(t["post_count"] / total_topic_posts * 100, 1) if total_topic_posts else 0.0

    # 7. Trend history — TIME-ORDERED decay simulation
    # Take top 15 posts, sort by timestamp (oldest first), build realistic curves
    history_source = sorted(top_trends[:15], key=lambda x: x.get("hours_old", 0), reverse=True)
    trend_history = []
    for i, p in enumerate(history_source):
        score = p.get("trend_score", 0.0)
        hours_old = p.get("hours_old", 0.0)
        is_spike = p.get("is_spike", False)
        eng = p.get("engagement") or {}
        total_eng = (eng.get("likes", 0) or 0) + (eng.get("comments", 0) or 0) + (eng.get("shares", 0) or 0) if isinstance(eng, dict) else 0

        # Build 8-point decay curve for this post (condensed for chart)
        decay = _build_decay_series(score, min(hours_old, 23), is_spike, n_points=8)
        prev = decay[-2] if len(decay) >= 2 else score
        momentum = round(decay[-1] - prev, 2)

        trend_history.append({
            "index": i + 1,
            "label": f"T{i+1}",
            "score": decay[-1],          # current (rightmost) value
            "peak": max(decay),
            "momentum": momentum,
            "decay_curve": decay,         # full 8-point curve for sparkline
            "is_spike": is_spike,
            "platform": p.get("platform", ""),
            "title": p.get("title", "")[:50],
            "sentiment": p.get("sentiment_label") or p.get("sentiment") or "neutral",
            "engagement": total_eng,
            "trend_phase": p.get("trend_phase", "Stable"),
            "virality_score": p.get("virality_score", 0.0),
            "timestamp": str(p.get("timestamp", "")),
        })

    # 8. Engagement totals
    total_engagement = 0
    async for doc in db.posts.aggregate([
        {"$match": filter_query},
        {"$group": {
            "_id": None,
            "likes": {"$sum": "$engagement.likes"},
            "comments": {"$sum": "$engagement.comments"},
            "shares": {"$sum": "$engagement.shares"},
        }}
    ]):
        total_engagement = (doc.get("likes") or 0) + (doc.get("comments") or 0) + (doc.get("shares") or 0)

    distinct_topics = await db.posts.distinct("topic", filter_query)
    topics_found = len([t for t in distinct_topics if t is not None])

    max_doc = await db.posts.find(filter_query).sort("trend_score", -1).limit(1).to_list(1)
    top_trend_score = min(max_doc[0].get("trend_score", 0.0), 9.8) if max_doc else 0.0

    # 9. AI Insights
    ai_insights = generate_ai_insights(top_trends[:50])

    # 10. Trend scores list (for backward compat)
    trend_scores_list = [
        {
            "title": p.get("title", "")[:50],
            "score": p.get("trend_score", 0.0),
            "platform": p.get("platform", ""),
            "is_spike": p.get("is_spike", False),
            "sentiment": p.get("sentiment_label") or p.get("sentiment") or "neutral",
            "engagement": (
                (p.get("engagement") or {}).get("likes", 0) +
                (p.get("engagement") or {}).get("comments", 0) +
                (p.get("engagement") or {}).get("shares", 0)
            ) if isinstance(p.get("engagement"), dict) else 0,
            "trend_phase": p.get("trend_phase", "Stable"),
            "virality_score": p.get("virality_score", 0.0),
        }
        for p in top_trends[:15]
    ]

    return {
        "total_posts": total_posts,
        "total_engagement": total_engagement,
        "topics_found": topics_found,
        "top_trend_score": round(top_trend_score, 2),
        "sentiment_distribution": sentiment_distribution,
        "platform_distribution": platform_distribution,
        "top_trends": top_trends,
        "topic_clusters": topic_clusters,
        "trend_scores": trend_scores_list,
        "trend_history": trend_history,
        "ai_insights": ai_insights,
        "last_updated": now.isoformat() + "Z",
    }
