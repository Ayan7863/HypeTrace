from datetime import datetime
from app.core.database import get_db
from app.schemas.trend import TrendPost


async def upsert_many(collection: str, posts: list[dict], id_field: str = "post_id"):
    db = get_db()
    col = db["posts"]
    for post in posts:
        try:
            # Ensure post is validated and normalized
            validated = TrendPost.model_validate(post)
            doc = validated.model_dump(by_alias=True)
            if doc.get("_id") is None:
                doc.pop("_id", None)
            
            # Deduplicate by post_id
            await col.update_one({"post_id": doc["post_id"]}, {"$set": doc}, upsert=True)
        except Exception as e:
            # Log error
            import logging
            logging.error(f"Error validating and upserting post in upsert_many: {e}")


async def find_many(collection: str, query: dict = {}, limit: int = 50, sort_by: str = "trend_score") -> list[dict]:
    db = get_db()
    col = db["posts"]
    
    # Map legacy collections and standard platforms to platform names
    platform_map = {
        "reddit_posts": "reddit",
        "reddit": "reddit",
        "twitter_posts": "twitter",
        "twitter": "twitter",
        "instagram_posts": "instagram",
        "instagram": "instagram",
        "trends": "youtube",
        "youtube": "youtube",
    }
    
    final_query = query.copy()
    if collection in platform_map:
        final_query["platform"] = platform_map[collection]
        
    cursor = col.find(final_query, {"embedding": 0, "embedding_vector": 0}).sort(sort_by, -1).limit(limit)
    docs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs


async def sentiment_stats(collection: str) -> dict:
    db = get_db()
    col = db["posts"]
    
    platform_map = {
        "reddit_posts": "reddit",
        "reddit": "reddit",
        "twitter_posts": "twitter",
        "twitter": "twitter",
        "instagram_posts": "instagram",
        "instagram": "instagram",
        "trends": "youtube",
        "youtube": "youtube",
    }
    
    match_stage = {}
    if collection in platform_map:
        match_stage = {"platform": platform_map[collection]}
        
    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})
    pipeline.append({"$group": {"_id": "$sentiment_label", "count": {"$sum": 1}}})
    
    stats = {"positive": 0, "negative": 0, "neutral": 0}
    async for doc in col.aggregate(pipeline):
        val = doc["_id"]
        if val in stats:
            stats[val] = doc["count"]
    return stats
