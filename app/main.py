from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from app.crud import create_friend, get_all_friends, get_friend
import os

app = FastAPI()

# Монтуємо папку для статичних файлів (фото)
app.mount("/media", StaticFiles(directory="app/storage/media"), name="media")

@app.post("/friends")
async def create_friend_endpoint(
    name: str = Form(...),
    profession: str = Form(...),
    profession_description: str | None = Form(None),
    photo: UploadFile = File(...)
):
    photo_data = await photo.read()
    friend = create_friend(name, profession, profession_description, photo_data)
    return friend

@app.get("/friends")
async def list_friends():
    return get_all_friends()

@app.get("/friends/{id}")
async def get_friend_endpoint(id: str):
    friend = get_friend(id)
    if not friend:
        raise HTTPException(404, "Друг не знайдений")
    return friend

@app.get("/media/{filename}")
async def get_media(filename: str):
    file_path = f"app/storage/media/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(404, "Файл не знайдено")
    return File(file_path)