from PIL import Image
import io
import uuid
import os

def create_friend(name: str, profession: str, profession_description: str | None, photo_data: bytes):
    # Перевірка: чи це валідне зображення
    try:
        img = Image.open(io.BytesIO(photo_data))
        img.verify()  # Перевірка на пошкодження
        img = Image.open(io.BytesIO(photo_data))  # Відкриваємо ще раз
    except Exception as e:
        raise ValueError(f"Файл не є зображенням: {e}")

    # Збереження
    os.makedirs("app/storage/media", exist_ok=True)
    friend_id = str(uuid.uuid4())
    photo_path = f"app/storage/media/{friend_id}.jpg"
    img.convert("RGB").save(photo_path, "JPEG")

    return {
        "id": friend_id,
        "name": name,
        "profession": profession,
        "profession_description": profession_description,
        "photo_url": f"/media/{friend_id}.jpg"
    }

# In-memory "база"
friends = {}

def get_all_friends():
    return list(friends.values())

def get_friend(friend_id: str):
    return friends.get(friend_id)