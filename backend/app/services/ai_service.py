import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from sklearn.cluster import KMeans
from collections import Counter
from datetime import datetime
import math
import re

_embedder: SentenceTransformer = None
_sentiment_pipeline = None

# ── Semantic topic category map ──────────────────────────────────────────────
_TOPIC_CATEGORIES = [
    ("AI & Machine Learning",    ["ai", "gpt", "llm", "model", "openai", "deepmind", "neural", "machine learning", "artificial intelligence", "transformer", "bert", "llama", "claude", "gemini"]),
    ("Cryptocurrency & Web3",    ["bitcoin", "crypto", "ethereum", "blockchain", "nft", "defi", "web3", "token", "btc", "eth", "solana", "binance"]),
    ("Space Exploration",        ["space", "nasa", "spacex", "rocket", "mars", "orbit", "satellite", "telescope", "webb", "starship", "astronaut"]),
    ("Cybersecurity",            ["hack", "breach", "vulnerability", "malware", "ransomware", "security", "exploit", "phishing", "zero-day", "cyber"]),
    ("Climate & Environment",    ["climate", "carbon", "emission", "solar", "renewable", "green", "warming", "environment", "fossil", "energy"]),
    ("Gaming & Esports",         ["game", "gaming", "esport", "playstation", "xbox", "nintendo", "steam", "fps", "rpg", "mmo", "twitch"]),
    ("Electric Vehicles & Tech", ["tesla", "electric", "vehicle", "ev", "battery", "charging", "autonomous", "self-driving", "fsd"]),
    ("Startups & Business",      ["startup", "funding", "venture", "ipo", "saas", "revenue", "mrr", "founder", "raise", "seed", "series"]),
    ("Health & Science",         ["health", "cancer", "vaccine", "study", "research", "medical", "drug", "clinical", "protein", "gene", "dna"]),
    ("Social Media & Culture",   ["viral", "trend", "meme", "influencer", "tiktok", "instagram", "twitter", "reddit", "youtube", "creator"]),
    ("Programming & Dev Tools",  ["python", "javascript", "rust", "golang", "react", "nextjs", "docker", "kubernetes", "github", "code", "developer"]),
    ("Politics & World News",    ["election", "president", "government", "policy", "war", "conflict", "senate", "congress", "vote", "law"]),
]


def _semantic_topic_label(texts: list[str]) -> str:
    """Score each category against the combined text and return the best match."""
    combined = " ".join(texts).lower()
    best_label, best_score = "General Trends", 0
    for label, keywords in _TOPIC_CATEGORIES:
        score = sum(combined.count(kw) for kw in keywords)
        if score > best_score:
            best_score, best_label = score, label
    return best_label


# ── Model loaders ─────────────────────────────────────────────────────────────
def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            truncation=True,
            max_length=512,
        )
    return _sentiment_pipeline


# ── Core ML functions ─────────────────────────────────────────────────────────
def compute_embeddings(texts: list[str]) -> list[list[float]]:
    embedder = get_embedder()
    return embedder.encode(texts, batch_size=32, show_progress_bar=False).tolist()


def compute_sentiment(texts: list[str]) -> list[dict]:
    pipe = get_sentiment_pipeline()
    results = []
    for text in texts:
        try:
            out = pipe(text[:512])[0]
            label = out["label"].lower()
            confidence = out["score"]
            if confidence < 0.65:
                results.append({"sentiment": "neutral", "sentiment_score": 0.0})
            else:
                score = confidence if label == "positive" else -confidence
                results.append({"sentiment": label, "sentiment_score": round(score, 4)})
        except Exception:
            results.append({"sentiment": "neutral", "sentiment_score": 0.0})
    return results


def compute_topics(texts: list[str], embeddings: list[list[float]]) -> tuple[list[int], list[str]]:
    """Cluster texts and assign semantic category labels to each cluster."""
    if len(texts) < 4:
        label = _semantic_topic_label(texts)
        return [0] * len(texts), [label] * len(texts)
    try:
        n_clusters = min(max(2, len(texts) // 5), 8)
        arr = np.array(embeddings)
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        cluster_ids = km.fit_predict(arr).tolist()

        cluster_map: dict[int, list[int]] = {}
        for i, c in enumerate(cluster_ids):
            cluster_map.setdefault(c, []).append(i)

        # Build semantic label per cluster
        cluster_labels: dict[int, str] = {}
        for cid, indices in cluster_map.items():
            cluster_texts = [texts[i] for i in indices]
            cluster_labels[cid] = _semantic_topic_label(cluster_texts)

        topic_labels = [cluster_labels[c] for c in cluster_ids]
        return cluster_ids, topic_labels
    except Exception:
        return [0] * len(texts), ["General Trends"] * len(texts)


# ── Trend score engine ────────────────────────────────────────────────────────
def _resolve_engagement(p: dict) -> tuple[int, int, int]:
    eng = p.get("engagement")
    if isinstance(eng, dict):
        return (
            int(eng.get("likes", 0) or 0),
            int(eng.get("comments", 0) or 0),
            int(eng.get("shares", 0) or 0),
        )
    likes = int(p.get("likes") or p.get("score") or 0)
    comments = int(p.get("comments") or p.get("comments_count") or p.get("replies") or 0)
    shares = int(p.get("shares") or p.get("retweets") or 0)
    return likes, comments, shares


def _resolve_timestamp(p: dict, now: datetime) -> datetime:
    ts = p.get("timestamp") or p.get("fetched_at") or p.get("created_utc") or p.get("created_at") or now
    if isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            ts = now
    elif isinstance(ts, (int, float)):
        try:
            ts = datetime.utcfromtimestamp(ts)
        except Exception:
            ts = now
    elif not isinstance(ts, datetime):
        ts = now
    if hasattr(ts, "tzinfo") and ts.tzinfo is not None:
        ts = ts.replace(tzinfo=None)
    return ts


def compute_trend_score_for_batch(posts: list[dict]) -> list[dict]:
    """
    trend_score = norm_engagement*0.35 + norm_velocity*0.30 + norm_sentiment*0.20 + recency*0.15
    Output range: 0–10, then percentile-stretched to 4.0–9.8 so scores feel realistic.
    Spike detection: posts with velocity > 2σ above mean get a +0.5 bonus (capped at 10).
    """
    if not posts:
        return posts

    now = datetime.utcnow()

    # ── Pass 1: raw values ────────────────────────────────────────────────────
    for p in posts:
        likes, comments, shares = _resolve_engagement(p)
        # Weight comments and shares more — they signal deeper engagement
        engagement = likes + comments * 1.5 + shares * 2.0
        p["_eng"] = engagement

        ts = _resolve_timestamp(p, now)
        hours = max(0.0, (now - ts).total_seconds() / 3600.0)
        p["_hours"] = hours

        # Velocity: engagement per hour (with smoothing)
        velocity = engagement / (hours + 2.0)
        p["_vel"] = velocity

    engs = [p["_eng"] for p in posts]
    vels = [p["_vel"] for p in posts]
    max_eng = max(engs) if engs else 1
    max_vel = max(vels) if vels else 1

    # Spike detection: velocity > mean + 2*std
    vel_arr = np.array(vels)
    vel_mean, vel_std = float(vel_arr.mean()), float(vel_arr.std()) if len(vels) > 1 else (0.0, 0.0)
    spike_threshold = vel_mean + 2.0 * vel_std

    # ── Pass 2: score ─────────────────────────────────────────────────────────
    raw_scores = []
    for p in posts:
        eng = p.pop("_eng")
        vel = p.pop("_vel")
        hours = p.pop("_hours")
        sentiment_score = float(p.get("sentiment_score") or 0.0)

        norm_eng = 10.0 * (math.log1p(eng) / math.log1p(max_eng + 1))
        norm_vel = 10.0 * (math.log1p(vel) / math.log1p(max_vel + 1))
        norm_sent = 10.0 * abs(sentiment_score)
        # Recency: half-life 36 hours
        recency = 10.0 * math.exp(-hours / 36.0)

        score = (
            norm_eng  * 0.35 +
            norm_vel  * 0.30 +
            norm_sent * 0.20 +
            recency   * 0.15
        )

        # Spike bonus
        if vel > spike_threshold:
            score = min(10.0, score + 0.5)

        p["_raw_score"] = score
        p["is_spike"] = vel > spike_threshold
        raw_scores.append(score)

    # ── Pass 3: percentile stretch to 4.0–9.8 ────────────────────────────────
    arr = np.array(raw_scores)
    s_min, s_max = arr.min(), arr.max()

    for p in posts:
        raw = p.pop("_raw_score")
        if s_max > s_min:
            # Linear stretch into [4.0, 9.8]
            stretched = 4.0 + (raw - s_min) / (s_max - s_min) * 5.8
        else:
            stretched = 6.5
        p["trend_score"] = round(max(4.0, min(9.8, stretched)), 2)

    return posts


# ── AI Insights ───────────────────────────────────────────────────────────────
def generate_ai_insights(posts: list[dict]) -> dict:
    """Generate structured investor-grade AI insights from analyzed posts."""
    if not posts:
        return {"summary": "No data available.", "opportunities": [], "pain_points": [], "recommendations": [], "market_predictions": []}

    sentiments = [p.get("sentiment_label") or p.get("sentiment") or "neutral" for p in posts]
    pos_count = sentiments.count("positive")
    neg_count = sentiments.count("negative")
    total = len(posts)

    platform_counts: dict[str, int] = {}
    for p in posts:
        plat = p.get("platform") or p.get("source") or "unknown"
        platform_counts[plat] = platform_counts.get(plat, 0) + 1
    top_platform = max(platform_counts, key=platform_counts.get) if platform_counts else "unknown"

    topic_counts: dict[str, int] = {}
    for p in posts:
        t = p.get("topic") or p.get("topic_label") or "General Trends"
        topic_counts[t] = topic_counts.get(t, 0) + 1
    top_topics = [t for t, _ in sorted(topic_counts.items(), key=lambda x: -x[1])[:3]]

    spikes = [p for p in posts if p.get("is_spike")]
    spike_titles = [p.get("title", "")[:55] for p in spikes[:2]]
    avg_score = round(sum(p.get("trend_score", 0) for p in posts) / total, 1)

    pos_pct = round(pos_count / total * 100)
    neg_pct = round(neg_count / total * 100)
    dominant = "positive" if pos_count > neg_count else "negative" if neg_count > pos_count else "mixed"

    summary = (
        f"Scanned {total} posts across {len(platform_counts)} platforms. "
        f"Overall sentiment is {dominant} — {pos_pct}% positive, {neg_pct}% negative. "
        f"Average trend score: {avg_score}/10. "
        f"Dominant topics: {', '.join(top_topics)}. "
        f"Highest activity on {top_platform.capitalize()}."
        + (f" {len(spikes)} viral spike{'s' if len(spikes) != 1 else ''} detected." if spikes else "")
    )

    opportunities, pain_points, recommendations, market_predictions = [], [], [], []

    topic_set = set(top_topics)

    if "AI & Machine Learning" in topic_set:
        opportunities.append("AI tooling demand is at an inflection point — developer communities show sustained high engagement, signaling a durable market shift.")
        recommendations.append("Launch AI-native developer tools or integrations now — the adoption curve is steep and early movers capture disproportionate mindshare.")
        market_predictions.append("AI infrastructure and tooling spend will continue accelerating over the next 6–12 months based on current engagement velocity.")
    if "Cryptocurrency & Web3" in topic_set:
        opportunities.append("Crypto narrative momentum is building — sentiment spikes often precede retail FOMO cycles by 2–4 weeks.")
        pain_points.append("Elevated volatility in crypto discourse signals fragile confidence — retail sentiment can reverse sharply on macro news.")
        market_predictions.append("Crypto engagement patterns suggest a potential breakout window; monitor on-chain metrics alongside social velocity.")
    if "Cybersecurity" in topic_set:
        pain_points.append("Security breach discussions are trending — enterprises face mounting pressure to demonstrate compliance and incident response capability.")
        recommendations.append("Security-focused SaaS and compliance tooling have a highly receptive B2B audience right now — ideal for outbound campaigns.")
        market_predictions.append("Cybersecurity budgets are likely to expand as breach frequency increases — a tailwind for security vendors.")
    if "Startups & Business" in topic_set:
        opportunities.append("Founder and investor communities are actively engaged — high-quality deal flow content and market maps will generate outsized reach.")
        market_predictions.append("Early-stage funding activity appears to be recovering based on social signal volume — watch for Series A announcements.")
    if "Health & Science" in topic_set:
        opportunities.append("Health-tech and biotech content is generating strong engagement — a signal of growing consumer interest in longevity and preventive care.")
        market_predictions.append("Digital health and AI diagnostics are emerging as the next high-growth vertical based on current topic momentum.")
    if "Space Exploration" in topic_set:
        opportunities.append("Space exploration content drives exceptional organic reach — ideal for science communicators and deep-tech investors.")
    if "Electric Vehicles & Tech" in topic_set:
        opportunities.append("EV discourse remains highly active — infrastructure, range anxiety, and software updates are the dominant pain points driving conversation.")
        market_predictions.append("EV adoption narratives will intensify around policy announcements and new model launches — track regulatory signals.")
    if "Programming & Dev Tools" in topic_set:
        recommendations.append("Developer tool launches and open-source releases are generating strong community traction — prioritize GitHub and Reddit distribution.")

    if neg_pct > 45:
        pain_points.append(f"Elevated negative sentiment ({neg_pct}%) indicates unmet expectations or active controversy — a potential reputational risk window for brands in these topics.")
    if pos_pct > 65:
        opportunities.append(f"Exceptionally strong positive sentiment ({pos_pct}%) creates a high-conversion window for product launches, partnerships, or fundraising announcements.")
    if spikes:
        opportunities.append(f"Viral spike in progress: '{spike_titles[0]}' — real-time engagement is accelerating. Act within 24–48 hours to maximize reach.")
    if avg_score >= 7.5:
        market_predictions.append(f"Current average trend score of {avg_score}/10 indicates a high-energy news cycle — expect elevated platform engagement for the next 24–72 hours.")

    if not opportunities:
        opportunities.append("Engagement is steady across platforms — a stable baseline suitable for consistent brand-building and content distribution.")
    if not pain_points:
        pain_points.append("No significant negative sentiment clusters detected — the current news cycle is relatively low-risk for brand exposure.")
    if not recommendations:
        recommendations.append("Increase AI analysis frequency to 2–4x daily to capture emerging micro-trends before they reach mainstream saturation.")
    if not market_predictions:
        market_predictions.append("Current data suggests a consolidation phase — monitor for breakout signals over the next 48–72 hours.")

    return {
        "summary": summary,
        "opportunities": opportunities[:3],
        "pain_points": pain_points[:3],
        "recommendations": recommendations[:3],
        "market_predictions": market_predictions[:2],
        "dominant_sentiment": dominant,
        "top_topics": top_topics,
        "spike_count": len(spikes),
        "avg_trend_score": avg_score,
    }


# ── Full pipeline ─────────────────────────────────────────────────────────────
def generate_summary(topic_label: str, posts: list[dict]) -> str:
    sentiments = [p.get("sentiment_label", "neutral") for p in posts]
    pos = sentiments.count("positive")
    neg = sentiments.count("negative")
    sources = list({p["platform"] for p in posts if p.get("platform")})
    dominant = "positive" if pos > neg else "negative" if neg > pos else "mixed"
    avg_score = round(sum(p.get("trend_score", 0) for p in posts) / len(posts), 1) if posts else 0.0
    return (
        f"'{topic_label}' — {len(posts)} posts across {', '.join(sources)}. "
        f"Sentiment: {dominant} ({pos}↑ {neg}↓). Avg score: {avg_score}."
    )


def run_full_analysis(posts: list[dict]) -> list[dict]:
    if not posts:
        return posts

    texts = [f"{p.get('title', '')} {p.get('content', '')}" for p in posts]

    embeddings = compute_embeddings(texts)
    sentiments = compute_sentiment(texts)
    topics, topic_labels = compute_topics(texts, embeddings)

    for i, post in enumerate(posts):
        post["embedding"] = embeddings[i]
        post["embedding_vector"] = embeddings[i]
        post["sentiment"] = sentiments[i]["sentiment"]
        post["sentiment_label"] = sentiments[i]["sentiment"]
        post["sentiment_score"] = sentiments[i]["sentiment_score"]
        post["topic_cluster"] = int(topics[i])
        post["topic_label"] = topic_labels[i]
        post["topic"] = topic_labels[i]

    posts = compute_trend_score_for_batch(posts)
    return posts


# Backward-compat stubs
def compute_trend_score(score: float, engagement: int, sentiment_score: float) -> float:
    return 6.5

def normalize_trend_scores(posts: list[dict]) -> list[dict]:
    return posts
