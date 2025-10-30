# handler.py
import sys
import os
import logging

# Добавляем текущую директорию в Python path
sys.path.insert(0, os.path.dirname(__file__))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Логируем переменные при инициализации Lambda
logger.info("=== Lambda Cold Start ===")
logger.info(f"Python path: {sys.path[:3]}")
logger.info(f"Working dir: {os.getcwd()}")

# Проверяем переменные окружения
env_status = {
    "S3_BUCKET_NAME": bool(os.getenv("S3_BUCKET_NAME")),
    "DYNAMODB_TABLE_NAME": bool(os.getenv("DYNAMODB_TABLE_NAME")),
    "LLM_PROVIDER": os.getenv("LLM_PROVIDER"),
    "BACKEND_BASE_URL": bool(os.getenv("BACKEND_BASE_URL")),
}
logger.info(f"Environment: {env_status}")

try:
    # Импортируем FastAPI
    from app.main import app
    from mangum import Mangum

    # Создаем handler
    mangum_handler = Mangum(app, lifespan="off")

    # Логируем все зарегистрированные роуты
    logger.info("📋 Available routes:")
    for route in app.routes:
        if hasattr(route, 'methods'):
            logger.info(f"  {route.methods} {route.path}")

    logger.info("✅ App imported successfully")

except Exception as e:
    logger.error(f"❌ Failed to import app: {e}", exc_info=True)
    raise


def lambda_handler(event, context):
    """Lambda entry point"""
    path = event.get("path", "unknown")
    method = event.get("httpMethod", "unknown")
    logger.info(f"📨 Request: {method} {path}")

    # Логируем headers для отладки
    headers = event.get("headers", {})
    logger.info(f"📋 Content-Type: {headers.get('content-type', 'N/A')}")

    try:
        response = mangum_handler(event, context)
        status = response.get("statusCode", "unknown")
        logger.info(f"📤 Response: {status}")

        # Если 404, логируем подробности
        if status == 404:
            logger.warning(f"⚠️ 404 for {method} {path}")
            logger.warning(f"Body: {response.get('body', 'N/A')[:200]}")

        return response

    except Exception as e:
        logger.error(f"❌ Handler error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": f'{{"error": "Internal error: {str(e)[:100]}"}}'
        }