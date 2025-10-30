# app/routes/friends.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import logging

log = logging.getLogger(__name__)
router = APIRouter()

# Логируем инициализацию
log.info("🔧 Friends router initialized")


@router.post("/", summary="Add friend")
async def api_add_friend(
        name: str = Form(...),
        profession: str = Form(...),
        profession_description: Optional[str] = Form(None),
        photo: UploadFile = File(...)
):
    log.info(f"📝 ADD FRIEND: name={name}, profession={profession}")
    try:
        from services.friend_service import add_friend
        photo_bytes = await photo.read()
        log.info(f"📷 Photo size: {len(photo_bytes)} bytes")

        friend = await add_friend(name, profession, profession_description, photo_bytes)
        log.info(f"✅ ADD FRIEND OK: {friend['id']}")
        return friend
    except Exception as e:
        log.error(f"❌ ADD FRIEND ERROR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", summary="Get all friends")
async def api_get_friends():
    log.info("📋 GET FRIENDS")
    try:
        from services.friend_service import get_friends
        friends = await get_friends()
        log.info(f"✅ GET FRIENDS OK: {len(friends)} friends")
        return friends
    except Exception as e:
        log.error(f"❌ GET FRIENDS ERROR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{friend_id}", summary="Get friend by ID")
async def api_get_friend(friend_id: str):
    log.info(f"🔍 GET FRIEND: {friend_id}")
    try:
        from services.friend_service import get_friends
        friends = await get_friends()
        friend = next((f for f in friends if f['id'] == friend_id), None)

        if not friend:
            log.warning(f"⚠️ Friend not found: {friend_id}")
            raise HTTPException(status_code=404, detail="Friend not found")

        log.info(f"✅ GET FRIEND OK: {friend['name']}")
        return friend
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"❌ GET FRIEND ERROR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{friend_id}/ask", summary="Ask friend a question")
async def api_ask_friend(friend_id: str, data: dict):
    log.info(f"💬 ASK FRIEND: {friend_id}")
    question = data.get("question")
    if not question:
        log.error("❌ ASK FRIEND: no question")
        raise HTTPException(status_code=400, detail="Question required")

    log.info(f"❓ Question: {question[:50]}...")
    try:
        from services.friend_service import ask_friend
        answer = await ask_friend(friend_id, question)
        log.info(f"✅ ASK FRIEND OK: {answer[:50]}...")
        return {"answer": answer}
    except ValueError as e:
        log.warning(f"⚠️ Friend not found: {friend_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.error(f"❌ ASK FRIEND ERROR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Логируем все роуты этого роутера
log.info("📋 Friends router routes:")
for route in router.routes:
    log.info(f"  {route.path} - {route.methods if hasattr(route, 'methods') else 'N/A'}")