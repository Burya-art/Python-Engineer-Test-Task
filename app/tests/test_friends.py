import pytest
import sys
import os

# Додаємо /app у шлях
sys.path.insert(0, "/app")

from fastapi.testclient import TestClient
from app.main import app
from PIL import Image
import io

client = TestClient(app)

def test_create_friend_missing_fields():
    response = client.post("/friends")
    assert response.status_code == 422

def test_create_friend_invalid_photo():
    files = {'photo': ('test.txt', io.BytesIO(b"not an image"), 'text/plain')}
    data = {'name': 'Test', 'profession': 'Dev'}
    response = client.post("/friends", data=data, files=files)
    assert response.status_code == 400

def test_create_friend_success():
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)

    files = {'photo': ('test.jpg', buffer, 'image/jpeg')}
    data = {'name': 'John', 'profession': 'Engineer', 'profession_description': 'Good'}
    response = client.post("/friends", data=data, files=files)
    assert response.status_code == 200
    assert response.json()["name"] == "John"

def test_list_friends():
    response = client.get("/friends")
    assert response.status_code == 200
    assert isinstance(response.json(), list)