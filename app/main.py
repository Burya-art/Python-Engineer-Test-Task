# app/main.py
import os
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("mangum").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.routing import APIRoute

app = FastAPI(title="Friends Bot API", redirect_slashes=False)

@app.get("/")
def root():
    """Root endpoint"""
    return {"status": "ok", "message": "Friends Bot API"}


@app.get("/health")
def health():
    """Health check з детальною інформацією"""
    env_vars = {
        "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME", "NOT_SET"),
        "DYNAMODB_TABLE_NAME": os.getenv("DYNAMODB_TABLE_NAME", "NOT_SET"),
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "NOT_SET"),
        "BACKEND_BASE_URL": os.getenv("BACKEND_BASE_URL", "NOT_SET"),
        "has_telegram_token": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
    }

    logger.info(f"Health check - env: {env_vars}")

    required = ["S3_BUCKET_NAME", "DYNAMODB_TABLE_NAME", "LLM_PROVIDER"]
    missing = [var for var in required if os.getenv(var) == "NOT_SET" or not os.getenv(var)]

    if missing:
        logger.warning(f"Missing variables: {missing}")
        return {
            "status": "degraded",
            "missing": missing,
            "environment": env_vars
        }

    return {
        "status": "ok",
        "environment": env_vars
    }


# КРИТИЧНО: Подключаем роуты ДО создания app, а не в startup
logger.info("🔧 Loading routes...")

try:
    from app.routes import friends
    app.include_router(friends.router, prefix="/friends", tags=["friends"])
    logger.info("✅ Friends routes loaded")
except Exception as e:
    logger.error(f"❌ Failed to load routes: {e}", exc_info=True)
    raise

# Выводим все зарегистрированные маршруты
logger.info("📋 Registered routes:")
for route in app.routes:
    logger.info(f"  {route.path} - {route.methods if hasattr(route, 'methods') else 'N/A'}")