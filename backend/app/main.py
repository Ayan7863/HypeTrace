from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.database import connect_db, close_db
from app.core.indexes import create_indexes
from app.api.trends import router as trends_router
from app.api.reddit_routes import router as reddit_router
from app.api.twitter_routes import router as twitter_router
from app.api.unified_trends import router as unified_router
from app.api.instagram_routes import router as instagram_router
from app.api.dashboard import router as dashboard_router
from app.api.news_routes import router as news_router

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await create_indexes()
    yield
    await close_db()


app = FastAPI(
    title="HypeTrace AI",
    description="AI-powered social media trend intelligence API",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trends_router, prefix="/api")
app.include_router(reddit_router)
app.include_router(twitter_router)
app.include_router(unified_router)
app.include_router(instagram_router)
app.include_router(dashboard_router)
app.include_router(news_router)



@app.get("/health")
async def health():
    return {"status": "ok", "service": "HypeTrace AI", "version": "2.0.0"}
