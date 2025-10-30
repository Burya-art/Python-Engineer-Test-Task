# services/friend_service.py
import boto3
import uuid
import os
from services.llm import ask_llm  # Используем оригинальный llm.py
import logging

log = logging.getLogger(__name__)


def get_s3():
    log.info("INIT S3 CLIENT")
    return boto3.client('s3')


def get_dynamodb():
    log.info("INIT DYNAMODB")
    return boto3.resource('dynamodb')


async def add_friend(name: str, profession: str, profession_description: str | None, photo_bytes: bytes):
    log.info("ADD FRIEND SERVICE START")
    s3 = get_s3()
    dynamodb = get_dynamodb()
    table = dynamodb.Table(os.getenv("DYNAMODB_TABLE_NAME"))
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket or not table:
        log.error("S3 or DynamoDB not configured")
        raise ValueError("S3 or DynamoDB not configured")

    friend_id = f"friend_{uuid.uuid4().hex[:8]}"
    photo_key = f"photos/{friend_id}.jpg"

    log.info(f"Uploading photo to S3: {photo_key}")
    s3.put_object(Bucket=bucket, Key=photo_key, Body=photo_bytes, ContentType="image/jpeg")
    photo_url = f"https://{bucket}.s3.amazonaws.com/{photo_key}"

    item = {
        "id": friend_id,
        "name": name,
        "profession": profession,
        "profession_description": profession_description,
        "photo_url": photo_url
    }
    log.info(f"Saving to DynamoDB: {friend_id}")
    table.put_item(Item=item)
    log.info("ADD FRIEND SERVICE OK")
    return item


async def get_friends():
    log.info("GET FRIENDS SERVICE")
    dynamodb = get_dynamodb()
    table = dynamodb.Table(os.getenv("DYNAMODB_TABLE_NAME"))
    response = table.scan()
    items = response.get("Items", [])
    log.info(f"GET FRIENDS SERVICE: {len(items)}")
    return items


async def ask_friend(friend_id: str, question: str):
    log.info(f"ASK FRIEND SERVICE: {friend_id}, question: {question}")
    dynamodb = get_dynamodb()
    table = dynamodb.Table(os.getenv("DYNAMODB_TABLE_NAME"))
    response = table.get_item(Key={"id": friend_id})
    friend = response.get("Item")
    if not friend:
        log.error("Friend not found")
        raise ValueError("Friend not found")

    log.info(f"Found friend: {friend['name']}, profession: {friend['profession']}")
    answer = await ask_llm(friend["profession"], friend.get("profession_description"), question)
    log.info(f"ASK FRIEND SERVICE OK, answer length: {len(answer)}")
    return answer