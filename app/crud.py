import os
import uuid
from PIL import Image
from app.schemas import Friend

friends = {}

def create_friend(name: str, profession: str, profession_description: str | None, photo: bytes) -> Friend:
    try:
        img = Image.open(photo)
        img.close()
    except:
        raise ValueError("Файл не є зображенням")

    os.makedirs("app/storage/media", exist_ok=True)
    filename = f"{uuid.uuid4()}.{photo.filename.split('.')[-1]}"
    file_path = f"app/storage/media/{filename}"

    with open(file_path, "wb") as f:
        f.write(photo)

    id = str(uuid.uuid4())
    friend = Friend(
        id=id,
        name=name,
        profession=profession,
        profession_description=profession_description,
        photo_url=f"/media/{filename}"
    )
    friends[id] = friend
    return friend

def get_all_friends():
    return list(friends.values())

def get_friend(id: str):
    return friends.get(id)