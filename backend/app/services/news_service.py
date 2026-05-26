import httpx
import math
from datetime import datetime
from app.core.config import get_settings
from app.ml.sentiment import analyze_sentiment, extract_keywords, clean_text
from app.ml.embeddings import compute_embeddings, cluster_topics

settings = get_settings()

BASE = "https://newsapi.org/v2"
TOPICS = [
    "artificial intelligence", "technology", "machine learning",
    "climate change", "cryptocurrency", "cybersecurity", "space",
]


def _has_key() -> bool:
    k = settings.news_api_key
    return bool(k) and not k.startswith("your_")


def _parse_article(article: dict, topic: str) -> dict | None:
    title = article.get("title") or ""
    content = article.get("description") or article.get("content") or ""
    url = article.get("url") or ""
    if not title or title == "[Removed]":
        return None
    published = article.get("publishedAt", "")
    try:
        ts = datetime.fromisoformat(published.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        ts = datetime.utcnow()
    return {
        "platform": "news",
        "source": "news",
        "post_id": f"news_{abs(hash(url)) % 9999999}",
        "title": title,
        "content": content[:600],
        "author": article.get("author") or article.get("source", {}).get("name", "unknown"),
        "url": url,
        "engagement": {"likes": 0, "comments": 0, "shares": 0},
        "score": 0.0,
        "topic_query": topic,
        "timestamp": ts,
        "fetched_at": datetime.utcnow(),
    }


def _trend_score(sentiment_score: float, confidence: float) -> float:
    base = math.log1p(100)
    sentiment_boost = 1 + (sentiment_score * 0.3)
    return round(base * sentiment_boost * confidence, 4)


def _deduplicate(posts: list[dict]) -> list[dict]:
    seen, result = set(), []
    for p in posts:
        if p["post_id"] not in seen:
            seen.add(p["post_id"])
            result.append(p)
    return result


def _enrich(posts: list[dict]) -> list[dict]:
    if not posts:
        return posts
    texts = [f"{p['title']} {p['content']}" for p in posts]
    sentiments = analyze_sentiment(texts)
    embeddings = compute_embeddings(texts)
    _, topic_labels = cluster_topics(texts, embeddings)

    for i, post in enumerate(posts):
        post.update(sentiments[i])
        post["keywords"] = extract_keywords(clean_text(texts[i]))
        post["topic_label"] = topic_labels[i]
        post["embedding"] = embeddings[i]

    from app.services.ai_service import compute_trend_score_for_batch
    return compute_trend_score_for_batch(posts)


async def fetch_trending_news(limit: int = 30) -> list[dict]:
    if not _has_key():
        return []
    posts = []
    per_topic = max(3, limit // len(TOPICS) + 1)

    async with httpx.AsyncClient(timeout=15) as client:
        for topic in TOPICS:
            try:
                res = await client.get(
                    f"{BASE}/everything",
                    params={
                        "q": topic,
                        "language": "en",
                        "sortBy": "popularity",
                        "pageSize": per_topic,
                        "apiKey": settings.news_api_key,
                    },
                )
                if res.status_code == 200:
                    for article in res.json().get("articles", []):
                        parsed = _parse_article(article, topic)
                        if parsed:
                            posts.append(parsed)
            except Exception:
                continue

    posts = _deduplicate(posts)[:limit]
    return _enrich(posts)


async def fetch_top_headlines(limit: int = 20) -> list[dict]:
    if not _has_key():
        return []
    posts = []
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            res = await client.get(
                f"{BASE}/top-headlines",
                params={
                    "language": "en",
                    "pageSize": min(limit, 100),
                    "apiKey": settings.news_api_key,
                },
            )
            if res.status_code == 200:
                for article in res.json().get("articles", []):
                    parsed = _parse_article(article, "top-headlines")
                    if parsed:
                        posts.append(parsed)
        except Exception:
            pass
    return _enrich(_deduplicate(posts))


async def search_news(query: str, limit: int = 20) -> list[dict]:
    if not _has_key():
        return []
    posts = []
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            res = await client.get(
                f"{BASE}/everything",
                params={
                    "q": query,
                    "language": "en",
                    "sortBy": "relevancy",
                    "pageSize": min(limit, 100),
                    "apiKey": settings.news_api_key,
                },
            )
            if res.status_code == 200:
                for article in res.json().get("articles", []):
                    parsed = _parse_article(article, query)
                    if parsed:
                        posts.append(parsed)
        except Exception:
            pass
    return _enrich(_deduplicate(posts))
