from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
from dotenv import load_dotenv
import asyncio
import requests

# Завантажуємо .env
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

# Дебаг
print(f"DEBUG: BOT_TOKEN: {'OK' if BOT_TOKEN else 'НЕМАЄ'}")
print(f"DEBUG: BACKEND_URL: {BACKEND_URL}")

# Ініціалізація
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Стани
class AddFriend(StatesGroup):
    photo = State()
    name = State()
    profession = State()
    description = State()

# /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply(
        "Привіт! Я бот для управління друзями.\n\n"
        "Команди:\n"
        "/addfriend — додати друга\n"
        "/list — показати всіх\n"
        "/friend <id> — деталі друга"
    )

# /list
@router.message(Command("list"))
async def cmd_list(message: types.Message):
    try:
        resp = requests.get(f"{BACKEND_URL}/friends")
        if resp.status_code != 200:
            await message.reply("Помилка сервера.")
            return
        friends_list = resp.json()
        if not friends_list:
            await message.reply("Список порожній.")
            return

        text = "Твої друзі:\n\n"
        for f in friends_list:
            text += f"• {f['name']} — {f['profession']}\n  ID: `{f['id']}`\n\n"
        await message.reply(text, parse_mode="Markdown")
    except Exception as e:
        await message.reply("Не вдалося отримати список.")

# /friend <id>
@router.message(Command("friend"))
async def cmd_friend(message: types.Message, command: Command):
    if not command.args:
        await message.reply("Використовуй: /friend <id>")
        return

    friend_id = command.args.strip()
    try:
        resp = requests.get(f"{BACKEND_URL}/friends/{friend_id}")
        if resp.status_code == 404:
            await message.reply("Друг не знайдений.")
            return
        if resp.status_code != 200:
            await message.reply("Помилка сервера.")
            return

        friend = resp.json()
        photo_url = f"{BACKEND_URL}{friend['photo_url']}".replace("//", "/")
        caption = (
            f"*{friend['name']}*\n"
            f"Професія: {friend['profession']}\n"
            f"Опис: {friend.get('profession_description') or '—'}\n"
            f"ID: `{friend['id']}`"
        )
        await message.answer_photo(photo_url, caption=caption, parse_mode="Markdown")
    except Exception:
        await message.reply(f"Не вдалося завантажити фото.\n\n{caption}", parse_mode="Markdown")

# /addfriend
@router.message(Command("addfriend"))
async def cmd_addfriend(message: types.Message, state: FSMContext):
    await message.reply("Надішли фото друга:")
    await state.set_state(AddFriend.photo)

@router.message(AddFriend.photo, lambda m: m.photo)
async def add_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_bytes = await bot.download_file(file.file_path)
    await state.update_data(photo=photo_bytes.read())
    await message.reply("Введи ім'я:")
    await state.set_state(AddFriend.name)

@router.message(AddFriend.name)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("Введи професію:")
    await state.set_state(AddFriend.profession)

@router.message(AddFriend.profession)
async def add_profession(message: types.Message, state: FSMContext):
    await state.update_data(profession=message.text)
    await message.reply("Введи опис професії (або *пропусти*):", parse_mode="Markdown")
    await state.set_state(AddFriend.description)

@router.message(AddFriend.description)
async def add_description(message: types.Message, state: FSMContext):
    desc = message.text if message.text.lower() != "пропусти" else None
    data = await state.get_data()
    await state.clear()

    photo_bytes = data["photo"]
    files = {
        "photo": ("friend_photo.jpg", photo_bytes, "image/jpeg")
    }
    form = {
        "name": data["name"],
        "profession": data["profession"],
        "profession_description": desc or ""
    }

    try:
        resp = requests.post(
            f"{BACKEND_URL}/friends",
            data=form,
            files=files,
            timeout=10
        )
        if resp.status_code == 200:
            friend = resp.json()
            await message.reply(f"Додано!\nID: `{friend['id']}`", parse_mode="Markdown")
        else:
            error = resp.text[:200]
            await message.reply(f"Помилка сервера: {resp.status_code}\n{error}")
    except Exception as e:
        await message.reply(f"Не вдалося надіслати: {str(e)}")

# Запуск
async def main():
    print("Бот запущено...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())