import random
from datetime import datetime

MOCK_POSTS = [
    # Reddit
    {"source": "reddit", "title": "GPT-5 rumored to launch next month with multimodal reasoning", "content": "Sources close to OpenAI suggest GPT-5 will feature real-time web browsing and advanced reasoning capabilities.", "author": "u/techinsider", "subreddit": "technology"},
    {"source": "reddit", "title": "New open-source LLM beats GPT-4 on coding benchmarks", "content": "A team from MIT released an open-source model that outperforms GPT-4 on HumanEval and MBPP benchmarks.", "author": "u/ml_researcher", "subreddit": "MachineLearning"},
    {"source": "reddit", "title": "Tesla Full Self-Driving v13 impressions after 1000 miles", "content": "After extensive testing, FSD v13 shows massive improvement in urban environments but still struggles with construction zones.", "author": "u/evdriver99", "subreddit": "technology"},
    {"source": "reddit", "title": "Climate scientists warn 2024 will be hottest year on record", "content": "New data from NOAA confirms global temperatures are tracking 1.5°C above pre-industrial levels for the first time.", "author": "u/climate_watch", "subreddit": "science"},
    {"source": "reddit", "title": "Apple Vision Pro 2 leaks suggest 40% lighter design", "content": "CAD renders and supply chain sources point to a dramatically redesigned Vision Pro with improved battery life.", "author": "u/appleinsider", "subreddit": "technology"},
    {"source": "reddit", "title": "Rust overtakes Python as most loved language in Stack Overflow survey", "content": "For the 9th consecutive year Rust tops the most loved language list, but Python remains most used.", "author": "u/devnews", "subreddit": "programming"},
    {"source": "reddit", "title": "SpaceX Starship completes first successful orbital flight", "content": "Starship successfully completed a full orbital test flight and landed both the booster and upper stage.", "author": "u/space_fan", "subreddit": "science"},
    {"source": "reddit", "title": "Cyberpunk 2077 sequel officially announced at The Game Awards", "content": "CD Projekt Red revealed Project Orion, the sequel to Cyberpunk 2077, with a teaser trailer.", "author": "u/gamer_hub", "subreddit": "gaming"},
    {"source": "reddit", "title": "Bitcoin hits new all-time high above $100k", "content": "Bitcoin surpassed $100,000 for the first time driven by ETF inflows and institutional adoption.", "author": "u/crypto_daily", "subreddit": "technology"},
    {"source": "reddit", "title": "Meta releases Llama 4 with 1 trillion parameters", "content": "Meta's latest open-source model features mixture-of-experts architecture and outperforms Claude 3 on most benchmarks.", "author": "u/ai_news", "subreddit": "artificial"},

    # Twitter
    {"source": "twitter", "title": "AI is eating software. Every company will be an AI company in 5 years or won't exist.", "content": "AI is eating software. Every company will be an AI company in 5 years or won't exist. Thread on what this means for developers.", "author": "TechInsider", "subreddit": None},
    {"source": "twitter", "title": "Real-time voice cloning now under 100ms latency — the future of communication is here.", "content": "Researchers have achieved real-time voice cloning in under 100ms latency opening new possibilities for communication.", "author": "AINews", "subreddit": None},
    {"source": "twitter", "title": "Climate crisis accelerating faster than models predicted. Urgent action needed.", "content": "New data confirms global temperatures are tracking 1.5°C above pre-industrial levels for the first time in recorded history.", "author": "ClimateWatch", "subreddit": None},
    {"source": "twitter", "title": "Major cybersecurity breach affects 50M users across multiple platforms.", "content": "Security researchers have uncovered a major breach affecting over 50 million users. Immediate password changes recommended.", "author": "SecurityNews", "subreddit": None},

    # Instagram
    {"source": "instagram", "title": "Study: 8 hours of sleep improves cognitive performance by 34%.", "content": "A new meta-analysis of sleep studies reveals optimal sleep duration significantly impacts cognitive performance and productivity.", "author": "HealthScience", "subreddit": None},
    {"source": "instagram", "title": "Quantum computing achieves 1000 qubit milestone — RSA encryption has an expiry date.", "content": "IBM and Google researchers jointly announced a 1000 qubit quantum computing milestone that threatens current encryption standards.", "author": "QuantumLeap", "subreddit": None},
    {"source": "instagram", "title": "Web3 is dead. Long live AI agents — the next wave of the internet.", "content": "Venture capitalists are shifting focus from blockchain to autonomous AI agents as the next major computing paradigm.", "author": "TechVC", "subreddit": None},
    {"source": "instagram", "title": "Dune 3 officially greenlit — Denis Villeneuve returns to direct.", "content": "Warner Bros confirmed Dune Messiah adaptation is in development with the full cast returning for the third installment.", "author": "FilmNews", "subreddit": None},

    # YouTube
    {"source": "youtube", "title": "I Tested Every AI Coding Assistant in 2024 — The Results Shocked Me", "content": "Comprehensive comparison of GitHub Copilot, Cursor, Tabnine, and Amazon CodeWhisperer on real-world projects.", "author": "Fireship", "subreddit": None},
    {"source": "youtube", "title": "Building a Full-Stack App with Next.js 14 and AI in 1 Hour", "content": "Step-by-step tutorial building a production-ready AI-powered web application using Next.js App Router.", "author": "Theo - t3.gg", "subreddit": None},
    {"source": "youtube", "title": "The Truth About Electric Vehicles in 2024", "content": "After driving 10 different EVs across 5000 miles, here's what nobody tells you about electric vehicle ownership.", "author": "MKBHD", "subreddit": None},
]


def generate_mock_posts(limit: int = 20) -> list[dict]:
    # Hourly bucket: same post within the same hour = update, new hour = new post
    hour_bucket = datetime.utcnow().strftime("%Y%m%d%H")
    posts = []
    selected = random.sample(MOCK_POSTS, min(limit, len(MOCK_POSTS)))

    for item in selected:
        base_id = abs(hash(item['title'])) % 999999
        post_id = f"{item['source']}_{base_id}_{hour_bucket}"
        likes = random.randint(500, 150000)
        comments = random.randint(50, 20000)
        shares = random.randint(10, 5000)

        posts.append({
            "platform": item["source"],
            "source": item["source"],
            "post_id": post_id,
            "title": item["title"],
            "content": item["content"],
            "author": item["author"],
            "url": f"https://{item['source']}.com/post/{post_id}",
            "engagement": {
                "likes": likes,
                "comments": comments,
                "shares": shares
            },
            "score": float(likes),
            "timestamp": datetime.utcnow(),
            "fetched_at": datetime.utcnow(),
        })

    return posts
