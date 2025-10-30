# bot/main.py
import asyncio
from aiogram import Bot, Dispatcher
from bot.handlers import router
from dotenv import load_dotenv
import os

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()
dp.include_router(router)

if __name__ == "__main__":
    print("Бот запущен в режимі polling (тільки локально)...")
    asyncio.run(dp.start_polling(bot))