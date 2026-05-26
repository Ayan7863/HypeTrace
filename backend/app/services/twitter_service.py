import math
import random
from datetime import datetime
from app.ml.sentiment import analyze_sentiment, extract_keywords, clean_text
from app.ml.embeddings import compute_embeddings, cluster_topics

MOCK_TWEETS = [
    {"title": "GPT-5 rumored to launch next month with real-time multimodal reasoning", "author": "TechInsider"},
    {"title": "Bitcoin surpasses $100k for the first time — institutional adoption accelerating", "author": "CryptoNews"},
    {"title": "Tesla FSD v13 impressions after 1000 miles — massive improvement in urban driving", "author": "EVDriver"},
    {"title": "New open-source LLM beats GPT-4 on coding benchmarks — MIT releases weights", "author": "MLResearch"},
    {"title": "Climate scientists warn 2024 will be hottest year on record by wide margin", "author": "ClimateWatch"},
    {"title": "Apple Vision Pro 2 leaks suggest 40% lighter design with 3x better battery life", "author": "AppleInsider"},
    {"title": "SpaceX Starship completes first fully successful orbital flight and landing", "author": "SpaceNews"},
    {"title": "Cyberpunk 2077 sequel officially announced — Project Orion confirmed at Game Awards", "author": "GamingHub"},
    {"title": "Meta releases Llama 4 with 1 trillion parameters completely open source", "author": "AINews"},
    {"title": "Quantum computing achieves 1000 qubit milestone — RSA encryption at risk", "author": "QuantumLeap"},
    {"title": "Rust overtakes Python as most loved language in Stack Overflow survey 2024", "author": "DevNews"},
    {"title": "Major cybersecurity breach affects 50M users — change your passwords now", "author": "SecurityAlert"},
    {"title": "Google DeepMind AlphaFold 3 solves protein folding for all molecules", "author": "ScienceDaily"},
    {"title": "OpenAI launches o3 model — scores 87% on ARC-AGI benchmark", "author": "AIWeekly"},
    {"title": "Nvidia H200 GPU sells out instantly — AI compute demand hits all time high", "author": "TechCrunch"},
    {"title": "Sam Altman: AGI will be achieved within the next 3 years", "author": "FutureTech"},
    {"title": "Electric vehicle sales surpass gasoline cars in Europe for first time", "author": "GreenEnergy"},
    {"title": "GitHub Copilot now writes 46% of all code on the platform", "author": "DevReport"},
    {"title": "New study: social media use linked to 34% increase in anxiety among teens", "author": "HealthScience"},
    {"title": "Webb telescope discovers potential signs of life on exoplanet K2-18b", "author": "NASANews"},
]


def _trend_score(sentiment_score: float, confidence: float, engagement: int) -> float:
    base = math.log1p(engagement) * 0.4
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



def _build_mock_posts(limit: int) -> list[dict]:
    hour_bucket = datetime.utcnow().strftime("%Y%m%d%H")
    selected = random.sample(MOCK_TWEETS, min(limit, len(MOCK_TWEETS)))
    posts = []
    for item in selected:
        likes = random.randint(500, 80000)
        retweets = random.randint(100, 20000)
        replies = random.randint(50, 5000)
        base_id = abs(hash(item['title'])) % 99999999
        post_id = f"twitter_{base_id}_{hour_bucket}"
        posts.append({
            "platform": "twitter",
            "source": "twitter",
            "post_id": post_id,
            "title": item["title"],
            "content": item["title"],
            "author": item["author"],
            "url": f"https://twitter.com/search?q={item['title'][:30].replace(' ', '+')}",
            "engagement": {"likes": likes, "comments": replies, "shares": retweets},
            "score": float(likes),
            "timestamp": datetime.utcnow(),
            "fetched_at": datetime.utcnow(),
        })
    return posts


async def fetch_trending_tweets(limit: int = 30) -> list[dict]:
    posts = _build_mock_posts(limit)
    return _enrich(_deduplicate(posts))


async def search_tweets(query: str, limit: int = 20) -> list[dict]:
    query_lower = query.lower()
    matched = [t for t in MOCK_TWEETS if query_lower in t["title"].lower()]
    if not matched:
        matched = random.sample(MOCK_TWEETS, min(5, len(MOCK_TWEETS)))
    posts = []
    for item in matched[:limit]:
        likes = random.randint(100, 50000)
        retweets = random.randint(50, 10000)
        replies = random.randint(20, 2000)
        posts.append({
            "source": "twitter",
            "post_id": f"twitter_{abs(hash(item['title'])) % 99999999}",
            "title": item["title"],
            "content": item["title"],
            "author": item["author"],
            "url": f"https://twitter.com/search?q={query.replace(' ', '+')}",
            "score": float(likes),
            "engagement": likes + retweets + replies,
            "likes": likes,
            "retweets": retweets,
            "replies": replies,
            "created_at": datetime.utcnow().isoformat(),
            "fetched_at": datetime.utcnow(),
        })
    return _enrich(_deduplicate(posts))
