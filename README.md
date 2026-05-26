# HypeTrace AI 🔥

AI-powered social media trend intelligence platform that monitors, analyzes, and visualizes trending content from Reddit, X (Twitter), and YouTube.

---

## Tech Stack

| Layer      | Technology                                          |
|------------|-----------------------------------------------------|
| Frontend   | Next.js 14, TailwindCSS, Recharts, TypeScript       |
| Backend    | FastAPI, Python 3.11+                               |
| Database   | MongoDB (Motor async driver)                        |
| AI/ML      | Sentence Transformers, HuggingFace, BERTopic        |
| APIs       | Reddit (PRAW), Twitter v2 (Tweepy), YouTube Data v3 |

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── core/         # Config, DB connection
│   │   ├── schemas/      # Pydantic models
│   │   └── services/     # Business logic & AI pipeline
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── app/          # Next.js App Router pages
    │   ├── components/
    │   │   ├── charts/   # Recharts components
    │   │   └── ui/       # Reusable UI components
    │   ├── lib/          # API client
    │   └── types/        # TypeScript interfaces
    ├── package.json
    └── .env.local
```

---

## Setup

### 1. Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB running locally or MongoDB Atlas URI

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Copy and fill in your API keys
copy .env.example .env

uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Environment Variables

### Backend (`backend/.env`)

| Variable               | Description                        |
|------------------------|------------------------------------|
| `MONGODB_URL`          | MongoDB connection string          |
| `DB_NAME`              | Database name (default: hypetrace) |
| `REDDIT_CLIENT_ID`     | Reddit app client ID               |
| `REDDIT_CLIENT_SECRET` | Reddit app client secret           |
| `REDDIT_USER_AGENT`    | Reddit user agent string           |
| `TWITTER_BEARER_TOKEN` | Twitter API v2 bearer token        |
| `YOUTUBE_API_KEY`      | YouTube Data API v3 key            |
| `CORS_ORIGINS`         | Allowed frontend origins           |

### Frontend (`frontend/.env.local`)

| Variable               | Description              |
|------------------------|--------------------------|
| `NEXT_PUBLIC_API_URL`  | Backend API base URL     |

---

## API Endpoints

| Method | Endpoint                    | Description                        |
|--------|-----------------------------|------------------------------------|
| GET    | `/health`                   | Health check                       |
| POST   | `/api/trends/fetch`         | Fetch posts from social platforms  |
| POST   | `/api/trends/analyze`       | Run AI analysis on stored posts    |
| GET    | `/api/trends/`              | List all trend posts               |
| GET    | `/api/trends/topics`        | Get topic cluster summaries        |
| GET    | `/api/trends/stats/sentiment` | Sentiment distribution stats     |
| GET    | `/api/trends/stats/sources` | Posts count per source             |

---

## AI Pipeline

1. **Embeddings** — `all-MiniLM-L6-v2` generates 384-dim sentence embeddings
2. **Sentiment** — `distilbert-base-uncased-finetuned-sst-2-english` classifies positive/negative
3. **Topic Clustering** — BERTopic clusters posts into semantic topics using UMAP + HDBSCAN
4. **Trend Scoring** — Logarithmic formula combining score, engagement, and sentiment boost
5. **Normalization** — MinMaxScaler normalizes trend scores to 0–100 range

---

## Getting API Keys

- **Reddit**: https://www.reddit.com/prefs/apps → Create app (script type)
- **Twitter/X**: https://developer.twitter.com → Create project → Bearer Token
- **YouTube**: https://console.cloud.google.com → Enable YouTube Data API v3 → Create API Key
