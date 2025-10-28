from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from typing import List
from .crud import create_friend, get_all_friends, get_friend

app = FastAPI()


# ------------------------------------
# Доданий ендпоінт Health Check (GET + HEAD)
# ------------------------------------
@app.get("/health")
@app.head("/health")  # Дозволяємо HEAD-запит для Docker healthcheck
def health():
    """Перевіряє стан сервера."""
    return {"status": "OK"}


# ------------------------------------
# Існуючі ендпоінти
# ------------------------------------

@app.post("/friends", response_model=dict)
async def create_friend_endpoint(
    name: str = Form(...),
    profession: str = Form(...),
    profession_description: str = Form(None),
    photo: UploadFile = File(...)
):
    photo_data = await photo.read()
    if not photo_data:
        raise HTTPException(400, "Фото не передано")
    try:
        friend = create_friend(name, profession, profession_description, photo_data)
        return friend
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/friends", response_model=List[dict])
def list_friends():
    return get_all_friends()


@app.get("/friends/{friend_id}", response_model=dict)
def friend_detail(friend_id: str):
    friend = get_friend(friend_id)
    if not friend:
        raise HTTPException(404, "Друг не знайдений")
    return friend