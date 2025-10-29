from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from typing import List
from .crud import create_friend, get_all_friends, get_friend
from services.llm import ask_llm

app = FastAPI()


# ------------------------------------
# Health Check (GET + HEAD)
# ------------------------------------
@app.get("/health")
@app.head("/health")
def health():
    """Перевіряє стан сервера."""
    return {"status": "OK"}


# ------------------------------------
# CRUD
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


# ------------------------------------
# LLM: /ask
# ------------------------------------
@app.post("/friends/{friend_id}/ask")
async def ask_friend(friend_id: str, body: dict):
    friend = get_friend(friend_id)
    if not friend:
        raise HTTPException(404, "Друг не знайдений")

    question = body.get("question")
    if not question:
        raise HTTPException(400, "Питання обов'язкове")

    response = await ask_llm(
        profession=friend["profession"],
        description=friend.get("profession_description"),
        question=question
    )
    return {"answer": response}