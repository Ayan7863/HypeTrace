import httpx
import math
import random
import json
import re
from datetime import datetime
from app.ml.sentiment import analyze_sentiment, extract_keywords, clean_text
from app.ml.embeddings import compute_embeddings, cluster_topics

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

TRENDING_TAGS = [
    "artificialintelligence", "technology", "machinelearning",
    "crypto", "gaming", "climatechange", "cybersecurity",
    "space", "startup", "coding",
]

MOCK_INSTAGRAM = [
    {"title": "The future of AI is here — and it's more powerful than we imagined 🤖", "author": "@techvision", "tag": "artificialintelligence", "likes": 45200, "comments": 1230},
    {"title": "Just dropped my new coding tutorial on building AI apps from scratch 💻🔥", "author": "@devmaster", "tag": "coding", "likes": 32100, "comments": 876},
    {"title": "Climate change is real and we need to act NOW 🌍 #savetheplanet", "author": "@earthwatch", "tag": "climatechange", "likes": 89400, "comments": 3421},
    {"title": "Bitcoin just hit a new all-time high! Are you holding? 📈 #crypto", "author": "@cryptoking", "tag": "crypto", "likes": 67800, "comments": 4532},
    {"title": "New gaming setup complete 🎮 RTX 4090 + 4K monitor = perfection", "author": "@gamerpro", "tag": "gaming", "likes": 54300, "comments": 2109},
    {"title": "SpaceX launch was absolutely breathtaking 🚀 The future of humanity is in space", "author": "@spacelover", "tag": "space", "likes": 123000, "comments": 5670},
    {"title": "My startup just raised $2M seed round! Hard work pays off 🙌 #startup", "author": "@founderlife", "tag": "startup", "likes": 28900, "comments": 1876},
    {"title": "Cybersecurity tip: Always use 2FA. Hackers are getting smarter every day 🔐", "author": "@securitypro", "tag": "cybersecurity", "likes": 19800, "comments": 654},
    {"title": "Machine learning model I built predicts stock prices with 94% accuracy 📊", "author": "@mlresearcher", "tag": "machinelearning", "likes": 41200, "comments": 2341},
    {"title": "The iPhone 16 Pro camera is absolutely insane 📸 Shot on iPhone", "author": "@photographer", "tag": "technology", "likes": 98700, "comments": 6543},
    {"title": "AI art is taking over the creative world — is this the end of human artists? 🎨", "author": "@aiartist", "tag": "artificialintelligence", "likes": 76500, "comments": 8932},
    {"title": "Web3 gaming is the future — play to earn is changing lives 🎮💰", "author": "@web3gamer", "tag": "gaming", "likes": 23400, "comments": 987},
    {"title": "Solar panels on my house — electricity bill went from $300 to $12 ☀️", "author": "@greenliving", "tag": "climatechange", "likes": 145000, "comments": 7654},
    {"title": "Just launched my SaaS product — 0 to $10k MRR in 3 months 🚀 #startup", "author": "@saasfounder", "tag": "startup", "likes": 34500, "comments": 2345},
    {"title": "Quantum computing explained in 60 seconds ⚛️ The future is quantum", "author": "@quantumtech", "tag": "technology", "likes": 56700, "comments": 3210},
    {"title": "My ML model can detect cancer with 99% accuracy — this could save millions 🏥", "author": "@healthtech", "tag": "machinelearning", "likes": 234000, "comments": 12300},
    {"title": "Ethereum 2.0 staking rewards are insane right now 💎 #crypto #ethereum", "author": "@ethmaxi", "tag": "crypto", "likes": 43200, "comments": 2876},
    {"title": "NASA just released the most stunning image of a black hole ever captured 🌌", "author": "@nasafan", "tag": "space", "likes": 567000, "comments": 23400},
    {"title": "Built a full-stack app in 24 hours using AI tools only 🤯 #coding", "author": "@hackathon", "tag": "coding", "likes": 38900, "comments": 1654},
    {"title": "Zero-day vulnerability found in major banking apps — update NOW 🚨", "author": "@cybernews", "tag": "cybersecurity", "likes": 87600, "comments": 5432},
]


def _trend_score(likes: int, comments: int, sentiment_score: float) -> float:
    engagement = likes * 0.6 + comments * 1.2
    base = math.log1p(engagement) * 0.4
    sentiment_boost = 1 + (sentiment_score * 0.3)
    return round(base * sentiment_boost, 4)


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



async def _try_scrape_hashtag(tag: str, client: httpx.AsyncClient) -> list[dict]:
    """Try to scrape Instagram public hashtag page."""
    posts = []
    try:
        res = await client.get(
            f"https://www.instagram.com/explore/tags/{tag}/",
            headers=HEADERS,
            timeout=10,
            follow_redirects=True,
        )
        if res.status_code != 200:
            return []

        # Extract shared data JSON from page
        match = re.search(r"window\._sharedData\s*=\s*({.*?});</script>", res.text)
        if not match:
            return []

        data = json.loads(match.group(1))
        edges = (
            data.get("entry_data", {})
            .get("TagPage", [{}])[0]
            .get("graphql", {})
            .get("hashtag", {})
            .get("edge_hashtag_to_media", {})
            .get("edges", [])
        )

        for edge in edges[:5]:
            node = edge.get("node", {})
            caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
            caption = caption_edges[0]["node"]["text"] if caption_edges else f"#{tag} trending post"
            shortcode = node.get("shortcode", "")
            likes = node.get("edge_liked_by", {}).get("count", 0)
            comments = node.get("edge_media_to_comment", {}).get("count", 0)

            posts.append({
                "platform": "instagram",
                "source": "instagram",
                "post_id": f"instagram_{shortcode}",
                "title": caption[:120],
                "content": caption[:600],
                "author": f"#{tag}",
                "url": f"https://www.instagram.com/p/{shortcode}/",
                "engagement": {"likes": likes, "comments": comments, "shares": 0},
                "score": float(likes),
                "tag": tag,
                "timestamp": datetime.utcnow(),
                "fetched_at": datetime.utcnow(),
            })
    except Exception:
        pass
    return posts


def _build_mock_posts(limit: int) -> list[dict]:
    hour_bucket = datetime.utcnow().strftime("%Y%m%d%H")
    selected = random.sample(MOCK_INSTAGRAM, min(limit, len(MOCK_INSTAGRAM)))
    posts = []
    for item in selected:
        likes = item["likes"] + random.randint(-1000, 5000)
        comments = item["comments"] + random.randint(-100, 500)
        base_id = abs(hash(item['title'])) % 99999999
        post_id = f"instagram_{base_id}_{hour_bucket}"
        posts.append({
            "platform": "instagram",
            "source": "instagram",
            "post_id": post_id,
            "title": item["title"],
            "content": item["title"],
            "author": item["author"],
            "url": f"https://www.instagram.com/explore/tags/{item['tag']}/",
            "engagement": {"likes": likes, "comments": comments, "shares": 0},
            "score": float(likes),
            "tag": item["tag"],
            "timestamp": datetime.utcnow(),
            "fetched_at": datetime.utcnow(),
        })
    return posts


async def fetch_trending_instagram(limit: int = 30) -> list[dict]:
    posts = []

    # Try real scraping first
    async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
        for tag in TRENDING_TAGS[:5]:
            scraped = await _try_scrape_hashtag(tag, client)
            posts.extend(scraped)
            if len(posts) >= limit:
                break

    posts = _deduplicate(posts)

    # Fall back to mock if scraping blocked
    if len(posts) < 5:
        posts = _build_mock_posts(limit)

    return _enrich(_deduplicate(posts)[:limit])


async def search_instagram(query: str, limit: int = 20) -> list[dict]:
    tag = query.lower().replace(" ", "")
    posts = []

    async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
        posts = await _try_scrape_hashtag(tag, client)

    if not posts:
        matched = [p for p in MOCK_INSTAGRAM if query.lower() in p["title"].lower() or query.lower() in p["tag"]]
        if not matched:
            matched = random.sample(MOCK_INSTAGRAM, min(5, len(MOCK_INSTAGRAM)))
        posts = []
        for item in matched[:limit]:
            likes = item["likes"]
            comments = item["comments"]
            posts.append({
                "platform": "instagram",
                "source": "instagram",
                "post_id": f"instagram_{abs(hash(item['title'] + query)) % 99999999}",
                "title": item["title"],
                "content": item["title"],
                "author": item["author"],
                "url": f"https://www.instagram.com/explore/tags/{tag}/",
                "engagement": {"likes": likes, "comments": comments, "shares": 0},
                "score": float(likes),
                "tag": tag,
                "timestamp": datetime.utcnow(),
                "fetched_at": datetime.utcnow(),
            })

    return _enrich(_deduplicate(posts)[:limit])
