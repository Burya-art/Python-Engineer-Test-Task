from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import List
import os
from .crud import create_friend, get_all_friends, get_friend, friends

app = FastAPI()

# Створюємо папку для медіа
os.makedirs("app/storage/media", exist_ok=True)
app.mount("/media", StaticFiles(directory="app/storage/media"), name="media")

@app.post("/friends", response_model=dict)
async def create_friend_endpoint(
    name: str = Form(...),
    profession: str = Form(...),
    profession_description: str = Form(None),
    photo: UploadFile = File(...)
):
    photo_data = await photo.read()
    if not photo_data:
        raise HTTPException(status_code=400, detail="Фото не передано")

    try:
        friend = create_friend(name, profession, profession_description, photo_data)
        friends[friend["id"]] = friend
        return friend
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/friends", response_model=List[dict])
def list_friends():
    return get_all_friends()

@app.get("/friends/{friend_id}", response_model=dict)
def friend_detail(friend_id: str):
    friend = get_friend(friend_id)
    if not friend:
        raise HTTPException(status_code=404, detail="Друг не знайдений")
    return friend