# bot/handlers.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import httpx
import os
import logging

logger = logging.getLogger(__name__)

router = Router()
BACKEND_URL = os.getenv("BACKEND_BASE_URL")

if not BACKEND_URL:
    raise RuntimeError("BACKEND_BASE_URL не задан!")

logger.info(f"Backend URL: {BACKEND_URL}")


class AddFriend(StatesGroup):
    photo = State()
    name = State()
    profession = State()
    description = State()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"Command /start from user {message.from_user.id}")
    await message.answer(
        "Привіт! Я бот для збереження друзів...\n\n"
        "Команди:\n"
        "/addfriend — додати друга\n"
        "/friends — список друзів\n"
        "/ask <id> <питання> — запитати про друга"
    )


@router.message(Command("friends"))
async def cmd_friends(message: types.Message):
    logger.info(f"Command /friends from user {message.from_user.id}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BACKEND_URL}/friends/", timeout=10)
            if resp.status_code == 200:
                friends = resp.json()
            else:
                logger.error(f"Backend returned {resp.status_code}: {resp.text}")
                friends = []

        if not friends:
            await message.reply("Список порожній.")
            return

        text = "Твої друзі:\n"
        for f in friends:
            text += f"• {f['name']} ({f['profession']}) — ID: `{f['id']}`\n"
        await message.reply(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in /friends: {e}", exc_info=True)
        await message.reply(f"Помилка: {str(e)}")


@router.message(Command("addfriend"))
async def cmd_addfriend(message: types.Message, state: FSMContext):
    logger.info(f"Command /addfriend from user {message.from_user.id}")
    await message.reply("Надішли фото друга:")
    await state.set_state(AddFriend.photo)


@router.message(AddFriend.photo, F.photo)
async def add_photo(message: types.Message, state: FSMContext):
    logger.info(f"Received photo from user {message.from_user.id}")
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    photo_bytes = await message.bot.download_file(file.file_path)
    await state.update_data(photo=photo_bytes.read())
    await message.reply("Введи ім'я:")
    await state.set_state(AddFriend.name)


@router.message(AddFriend.name)
async def add_name(message: types.Message, state: FSMContext):
    logger.info(f"Received name from user {message.from_user.id}: {message.text}")
    await state.update_data(name=message.text)
    await message.reply("Введи професію:")
    await state.set_state(AddFriend.profession)


@router.message(AddFriend.profession)
async def add_profession(message: types.Message, state: FSMContext):
    logger.info(f"Received profession from user {message.from_user.id}: {message.text}")
    await state.update_data(profession=message.text)
    await message.reply("Введи опис професії (або 'пропусти'):")
    await state.set_state(AddFriend.description)


@router.message(AddFriend.description)
async def add_description(message: types.Message, state: FSMContext):
    logger.info(f"Received description from user {message.from_user.id}: {message.text}")
    desc = message.text if message.text.lower() != "пропусти" else None
    data = await state.get_data()
    await state.clear()

    files = {"photo": ("photo.jpg", data["photo"], "image/jpeg")}
    form = {
        "name": data["name"],
        "profession": data["profession"],
        "profession_description": desc or ""
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/friends/",
                data=form,
                files=files,
                timeout=30,
                follow_redirects=True
            )

        logger.info(f"Backend response: {resp.status_code}")

        if resp.status_code == 200:
            friend = resp.json()
            await message.reply(f"✅ Додано!\nID: <code>{friend['id']}</code>")
        else:
            logger.error(f"Backend error: {resp.status_code} - {resp.text}")
            await message.reply(f"❌ Помилка бекенда: {resp.status_code}\n{resp.text[:200]}")

    except httpx.TimeoutException:
        logger.error("Request timeout")
        await message.reply("⏰ Таймаут запиту до сервера")
    except Exception as e:
        logger.error(f"Error adding friend: {e}", exc_info=True)
        await message.reply(f"❌ Помилка: {str(e)}")


@router.message(Command("ask"))
async def cmd_ask(message: types.Message):
    logger.info(f"Command /ask from user {message.from_user.id}")
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        await message.reply("Використовуй: /ask <id> <питання>")
        return

    _, friend_id, question = parts

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}/friends/{friend_id}/ask",
                json={"question": question},
                timeout=15,
                follow_redirects=True
            )

        if resp.status_code == 404:
            await message.reply("❌ Друг не знайдений.")
            return
        elif resp.status_code != 200:
            logger.error(f"Ask endpoint error: {resp.status_code} - {resp.text}")
            await message.reply(f"❌ Помилка сервера: {resp.status_code}")
            return

        answer = resp.json().get("answer", "Немає відповіді.")
        await message.reply(f"*Відповідь:*\n{answer}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in /ask: {e}", exc_info=True)
        await message.reply(f"❌ Помилка: {str(e)}")