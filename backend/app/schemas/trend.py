from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any
from datetime import datetime


class EngagementSchema(BaseModel):
    likes: int = 0
    comments: int = 0
    shares: int = 0


class TrendPost(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    platform: str
    title: str
    text: Optional[str] = None
    content: str
    engagement: EngagementSchema = Field(default_factory=EngagementSchema)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    url: str = ""
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    topic: Optional[str] = None
    embedding_vector: Optional[list[float]] = None
    trend_score: Optional[float] = None

    # Legacy fields for backward compatibility
    source: Optional[str] = None
    post_id: Optional[str] = None
    author: Optional[str] = "unknown"
    sentiment: Optional[str] = None
    topic_label: Optional[str] = None
    topic_cluster: Optional[int] = None
    embedding: Optional[list[float]] = None
    fetched_at: Optional[datetime] = None
    score: Optional[float] = 0.0

    @model_validator(mode="before")
    @classmethod
    def populate_unified_and_legacy_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # 1. Map/Normalize platform names
        src = data.get("source") or data.get("platform") or "reddit"
        src_lower = str(src).lower().strip()
        if src_lower in ("x", "twitter", "twitter_posts"):
            platform = "twitter"
        elif src_lower in ("insta", "instagram", "instagram_posts"):
            platform = "instagram"
        elif src_lower in ("yt", "youtube", "trends"):
            platform = "youtube"
        elif src_lower in ("news", "news_posts"):
            platform = "news"
        else:
            platform = "reddit"

        data["platform"] = platform
        data["source"] = platform

        # 2. Normalize title / text
        title = data.get("title") or data.get("text") or ""
        data["title"] = title
        data["text"] = title

        # 3. Normalize engagement
        eng = data.get("engagement")
        if not isinstance(eng, dict):
            # Parse from flat fields
            likes = int(data.get("likes") or data.get("score") or 0)
            eng_val = eng if isinstance(eng, (int, float)) else 0
            comments = int(data.get("comments") or data.get("comments_count") or data.get("replies") or data.get("num_comments") or eng_val)
            shares = int(data.get("shares") or data.get("retweets") or 0)
            data["engagement"] = {"likes": likes, "comments": comments, "shares": shares}
        else:
            # ensure standard keys
            likes = int(eng.get("likes") or 0)
            comments = int(eng.get("comments") or 0)
            shares = int(eng.get("shares") or 0)
            data["engagement"] = {"likes": likes, "comments": comments, "shares": shares}

        # Set flat fields/legacy counts
        data["score"] = float(likes)
        data["engagement_count"] = likes + comments + shares

        # 4. Normalize timestamp
        ts = data.get("timestamp") or data.get("fetched_at") or data.get("created_utc") or data.get("created_at") or datetime.utcnow()
        if isinstance(ts, str):
            try:
                # Remove Z and offset if any
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.utcnow()
        elif isinstance(ts, (int, float)):
            try:
                ts = datetime.utcfromtimestamp(ts)
            except Exception:
                ts = datetime.utcnow()
        data["timestamp"] = ts
        data["fetched_at"] = ts

        # 5. Sentiment
        sentiment_label = data.get("sentiment_label") or data.get("sentiment")
        data["sentiment_label"] = sentiment_label
        data["sentiment"] = sentiment_label

        # 6. Topic
        topic = data.get("topic") or data.get("topic_label")
        data["topic"] = topic
        data["topic_label"] = topic

        # 7. Embedding
        emb = data.get("embedding_vector") or data.get("embedding")
        data["embedding_vector"] = emb
        data["embedding"] = emb

        # 8. Post ID
        pid = data.get("post_id") or data.get("id") or f"{platform}_{abs(hash(title)) % 999999}"
        data["post_id"] = pid
        data["id"] = pid

        return data

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class TrendSummary(BaseModel):
    topic_label: str
    post_count: int
    avg_sentiment: float
    avg_trend_score: float
    top_sources: list[str]
    summary: str


class FetchRequest(BaseModel):
    sources: list[str] = ["reddit", "twitter", "youtube", "instagram"]
    limit: int = 20


class AnalyzeRequest(BaseModel):
    recompute: bool = False

