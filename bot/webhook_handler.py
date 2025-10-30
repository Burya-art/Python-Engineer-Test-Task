# bot/webhook_handler.py
import json
import asyncio
import os
import logging
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set!")

logger.info(f"✅ Bot token loaded: {TELEGRAM_BOT_TOKEN[:20]}...")

# Глобальные объекты
bot = None
dp = None
loop = None


def get_event_loop():
    """Получаем или создаем event loop для Lambda"""
    global loop

    if loop is None or loop.is_closed():
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        logger.info("🔧 Event loop created")

    return loop


def get_bot_and_dp():
    """Инициализация бота и диспетчера"""
    global bot, dp

    if bot is None:
        logger.info("🔧 Initializing bot...")
        session = AiohttpSession()
        bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
        logger.info("✅ Bot initialized")

    if dp is None:
        logger.info("🔧 Initializing dispatcher...")
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        try:
            from bot.handlers import router as bot_router
            dp.include_router(bot_router)
            logger.info("✅ Bot handlers loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load handlers: {e}", exc_info=True)
            raise

    return bot, dp


async def process_update(update_dict: dict):
    """Обработка update от Telegram"""
    bot, dp = get_bot_and_dp()

    try:
        logger.info(f"📥 Processing update: {update_dict.get('update_id')}")

        if "update_id" not in update_dict:
            raise ValueError("Missing update_id in update")

        update = types.Update(**update_dict)
        logger.info(f"✅ Update parsed: {update.update_id}")

        await dp.feed_update(bot=bot, update=update)
        logger.info(f"✅ Update {update.update_id} processed successfully")

    except Exception as e:
        logger.error(f"❌ Error processing update: {e}", exc_info=True)
        raise


def lambda_handler(event, context):
    """Lambda entry point для webhook"""
    logger.info("=" * 50)
    logger.info("🚀 Webhook triggered")
    logger.info(f"Method: {event.get('httpMethod')}, Path: {event.get('path')}")

    try:
        # Парсим body
        body = event.get("body", "{}")
        logger.info(f"📦 Body type: {type(body)}")

        if isinstance(body, str):
            if not body or body == "{}":
                logger.warning("⚠️ Empty body received")
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"ok": True, "message": "Empty body"})
                }
            body = json.loads(body)

        logger.info(f"📋 Body keys: {list(body.keys())}")

        if "update_id" not in body:
            logger.error(f"❌ Invalid update format: {body}")
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Invalid update format"})
            }

        # КРИТИЧНО: используем существующий loop вместо asyncio.run()
        loop = get_event_loop()
        loop.run_until_complete(process_update(body))

        logger.info("✅ Webhook processed successfully")
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True})
        }

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parse error: {e}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"JSON parse error: {str(e)}"})
        }

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)[:200]})
        }

    finally:
        logger.info("=" * 50)