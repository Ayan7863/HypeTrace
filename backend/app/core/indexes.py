from app.core.database import get_db


async def create_indexes():
    db = get_db()
    col = db["posts"]
    await col.create_index("post_id", unique=True)
    await col.create_index("platform")
    await col.create_index("sentiment_label")
    await col.create_index([("trend_score", -1)])
    await col.create_index([("timestamp", -1)])
    await col.create_index([("platform", 1), ("trend_score", -1)])
    await col.create_index([("platform", 1), ("sentiment_label", 1)])
    await col.create_index("topic")
    # TTL: auto-delete posts older than 7 days
    await col.create_index("fetched_at", expireAfterSeconds=7 * 24 * 3600)
