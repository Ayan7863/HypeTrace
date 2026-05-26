from datetime import datetime
from app.core.database import get_db
from app.schemas.trend import TrendPost

COLLECTION = "posts"


async def upsert_posts(posts: list[dict]):
    db = get_db()
    col = db[COLLECTION]
    inserted = 0
    updated = 0
    errors = 0
    for post in posts:
        try:
            validated = TrendPost.model_validate(post)
            doc = validated.model_dump(by_alias=True)
            if doc.get("_id") is None:
                doc.pop("_id", None)
            result = await col.update_one(
                {"post_id": doc["post_id"]},
                {"$set": doc},
                upsert=True,
            )
            if result.upserted_id:
                inserted += 1
            else:
                updated += 1
        except Exception as e:
            import logging
            logging.error(f"upsert_posts error for post '{post.get('title', '')[:40]}': {e}")
            errors += 1
    import logging
    logging.info(f"upsert_posts: new={inserted}, updated={updated}, errors={errors}")
    return {"inserted": inserted, "updated": updated, "errors": errors}


async def get_all_posts(limit: int = 100, source: str = None) -> list[dict]:
    db = get_db()
    col = db[COLLECTION]
    
    query = {}
    if source:
        s_lower = source.lower().strip()
        if s_lower in ("x", "twitter"):
            query["platform"] = "twitter"
        elif s_lower in ("insta", "instagram"):
            query["platform"] = "instagram"
        elif s_lower in ("yt", "youtube"):
            query["platform"] = "youtube"
        elif s_lower == "news":
            query["platform"] = "news"
        else:
            query["platform"] = s_lower
            
    cursor = col.find(query, {"embedding": 0, "embedding_vector": 0}).sort("trend_score", -1).limit(limit)
    posts = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        # Ensure backward compatibility keys
        doc["id"] = doc.get("post_id")
        doc["source"] = doc.get("platform")
        doc["sentiment"] = doc.get("sentiment_label")
        doc["topic_label"] = doc.get("topic")
        posts.append(doc)
    return posts


async def get_topic_summaries() -> list[dict]:
    db = get_db()
    col = db[COLLECTION]
    pipeline = [
        {"$match": {"topic": {"$ne": None}}},
        {"$group": {
            "_id": "$topic",
            "post_count": {"$sum": 1},
            "avg_sentiment": {"$avg": "$sentiment_score"},
            "avg_trend_score": {"$avg": "$trend_score"},
            "sources": {"$addToSet": "$platform"},
        }},
        {"$sort": {"avg_trend_score": -1}},
        {"$limit": 20}
    ]
    results = []
    async for doc in col.aggregate(pipeline):
        label = doc["_id"]
        if label:
            results.append({
                "topic_label": label,
                "post_count": doc["post_count"],
                "avg_sentiment": round(doc["avg_sentiment"] or 0.0, 3),
                "avg_trend_score": round(doc["avg_trend_score"] or 0.0, 2),
                "top_sources": list(doc["sources"]),
            })
    return results


async def get_sentiment_stats() -> dict:
    db = get_db()
    stats = {"positive": 0, "negative": 0, "neutral": 0}
    col = db[COLLECTION]
    async for doc in col.aggregate([{"$group": {"_id": "$sentiment_label", "count": {"$sum": 1}}}]):
        lbl = doc["_id"]
        if lbl in stats:
            stats[lbl] = doc["count"]
    return stats


async def get_source_stats() -> list[dict]:
    db = get_db()
    col = db[COLLECTION]
    pipeline = [
        {"$group": {
            "_id": "$platform",
            "count": {"$sum": 1},
            "avg_trend_score": {"$avg": "$trend_score"}
        }}
    ]
    counts = []
    async for doc in col.aggregate(pipeline):
        plat = doc["_id"]
        if plat:
            counts.append({
                "source": plat,
                "count": doc["count"],
                "avg_trend_score": round(doc["avg_trend_score"] or 0.0, 2)
            })
            
    # Guarantee all standardized platforms are represented
    all_platforms = ["reddit", "twitter", "youtube", "instagram", "news"]
    existing_platforms = {item["source"] for item in counts}
    for p in all_platforms:
        if p not in existing_platforms:
            counts.append({
                "source": p,
                "count": 0,
                "avg_trend_score": 0.0
            })
            
    return counts
