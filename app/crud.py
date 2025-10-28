import boto3
import uuid
import os
from PIL import Image
import io
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv  # ДОДАЙ ЦЕ

# ЗАВАНТАЖУЙ .env ТУТ
load_dotenv()

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS налаштування
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "testtask-friends-photos")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "FriendsTable")

logger.info(f"Завантажено AWS_ACCESS_KEY_ID: {'Так' if AWS_ACCESS_KEY_ID else 'Ні'}")
logger.info(f"Завантажено AWS_SECRET_ACCESS_KEY: {'Так' if AWS_SECRET_ACCESS_KEY else 'Ні'}")
logger.info(f"S3 Bucket: {S3_BUCKET_NAME}")
logger.info(f"DynamoDB Table: {DYNAMODB_TABLE_NAME}")

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    logger.error("AWS ключі не знайдені в .env!")
    raise RuntimeError("AWS ключі не знайдені")

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)
s3 = session.client("s3")
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)
bucket_name = S3_BUCKET_NAME

# Перевірка підключення
try:
    s3.head_bucket(Bucket=bucket_name)
    logger.info("S3: бакет доступний")
except Exception as e:
    logger.error(f"S3: помилка бакета: {e}")

try:
    table.load()
    logger.info("DynamoDB: таблиця доступна")
except Exception as e:
    logger.error(f"DynamoDB: помилка таблиці: {e}")

# === create_friend ===
def create_friend(name: str, profession: str, profession_description: str | None, photo_data: bytes) -> Dict:
    logger.info(f"create_friend: start | name={name}")

    try:
        img = Image.open(io.BytesIO(photo_data))
        img.verify()
        img = Image.open(io.BytesIO(photo_data))
        logger.info(f"Зображення OK: {img.size}")
    except Exception as e:
        logger.error(f"Зображення помилка: {e}")
        raise ValueError(f"Файл не є зображенням: {e}")

    friend_id = str(uuid.uuid4())
    photo_key = f"{friend_id}.jpg"

    img_buffer = io.BytesIO()
    img.convert("RGB").save(img_buffer, format="JPEG")
    img_buffer.seek(0)

    try:
        s3.upload_fileobj(img_buffer, bucket_name, photo_key, ExtraArgs={"ContentType": "image/jpeg"})
        logger.info("S3: завантажено")
    except Exception as e:
        logger.error(f"S3 помилка: {e}")
        raise
    finally:
        img_buffer.close()

    photo_url = f"https://{bucket_name}.s3.amazonaws.com/{photo_key}"

    item = {
        "id": friend_id,
        "name": name,
        "profession": profession,
        "profession_description": profession_description or "",
        "photo_url": photo_url
    }

    try:
        table.put_item(Item=item)
        logger.info("DynamoDB: збережено")
    except Exception as e:
        logger.error(f"DynamoDB помилка: {e}")
        raise

    logger.info("create_friend: УСПІХ")
    return item

# === get_all_friends ===
def get_all_friends() -> List[Dict]:
    try:
        response = table.scan()
        items = response.get("Items", [])
        logger.info(f"get_all_friends: {len(items)} друзів")
        return items
    except Exception as e:
        logger.error(f"get_all_friends помилка: {e}")
        return []

# === get_friend ===
def get_friend(friend_id: str) -> Optional[Dict]:
    try:
        response = table.get_item(Key={"id": friend_id})
        item = response.get("Item")
        logger.info(f"get_friend: {'знайдено' if item else 'немає'}")
        return item
    except Exception as e:
        logger.error(f"get_friend помилка: {e}")
        return None