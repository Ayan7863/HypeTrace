import httpx
import math
from datetime import datetime
from app.ml.sentiment import analyze_sentiment, extract_keywords, clean_text
from app.ml.embeddings import compute_embeddings, cluster_topics

HEADERS = {"User-Agent": "Mozilla/5.0 HypeTrace/1.0"}
BASE = "https://www.reddit.com"

SUBREDDITS = [
    "technology", "artificial", "MachineLearning",
    "worldnews", "gaming", "science", "programming", "business",
]


def _parse_post(p: dict, subreddit: str) -> dict:
    likes = int(p.get("score", 0))
    comments = int(p.get("num_comments", 0))
    return {
        "platform": "reddit",
        "source": "reddit",
        "post_id": f"reddit_{p['id']}",
        "title": p.get("title", ""),
        "content": p.get("selftext", "")[:600] or p.get("title", ""),
        "author": p.get("author", "unknown"),
        "url": f"{BASE}{p.get('permalink', '')}",
        "subreddit": subreddit,
        "engagement": {"likes": likes, "comments": comments, "shares": 0},
        "score": float(likes),
        "upvote_ratio": float(p.get("upvote_ratio", 0)),
        "timestamp": datetime.utcfromtimestamp(p.get("created_utc", 0)),
        "fetched_at": datetime.utcnow(),
    }


def _trend_score(score: float, engagement: int, sentiment_score: float, upvote_ratio: float) -> float:
    base = math.log1p(score) * 0.4 + math.log1p(engagement) * 1.5 * 0.3
    sentiment_boost = 1 + (sentiment_score * 0.3)
    ratio_boost = upvote_ratio if upvote_ratio > 0 else 0.5
    return round(base * sentiment_boost * ratio_boost, 4)


def _deduplicate(posts: list[dict]) -> list[dict]:
    seen, result = set(), []
    for p in posts:
        key = p["post_id"]
        if key not in seen:
            seen.add(key)
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


async def fetch_hot_posts(limit: int = 30) -> list[dict]:
    posts = []
    per_sub = max(5, limit // len(SUBREDDITS) + 1)
    async with httpx.AsyncClient(headers=HEADERS, timeout=12, follow_redirects=True) as client:
        for sub in SUBREDDITS:
            try:
                res = await client.get(f"{BASE}/r/{sub}/hot.json?limit={per_sub}")
                if res.status_code == 200:
                    for child in res.json()["data"]["children"]:
                        posts.append(_parse_post(child["data"], sub))
            except Exception:
                continue
    posts = _deduplicate(posts)[:limit]
    return _enrich(posts)


async def fetch_top_posts(subreddit: str = "all", time_filter: str = "day", limit: int = 20) -> list[dict]:
    posts = []
    async with httpx.AsyncClient(headers=HEADERS, timeout=12, follow_redirects=True) as client:
        try:
            res = await client.get(f"{BASE}/r/{subreddit}/top.json?t={time_filter}&limit={limit}")
            if res.status_code == 200:
                for child in res.json()["data"]["children"]:
                    posts.append(_parse_post(child["data"], subreddit))
        except Exception:
            pass
    return _enrich(_deduplicate(posts))


async def search_posts(query: str, limit: int = 20) -> list[dict]:
    posts = []
    async with httpx.AsyncClient(headers=HEADERS, timeout=12, follow_redirects=True) as client:
        try:
            res = await client.get(
                f"{BASE}/search.json",
                params={"q": query, "sort": "relevance", "limit": limit, "type": "link"},
            )
            if res.status_code == 200:
                for child in res.json()["data"]["children"]:
                    p = child["data"]
                    posts.append(_parse_post(p, p.get("subreddit", "unknown")))
        except Exception:
            pass
    return _enrich(_deduplicate(posts))
