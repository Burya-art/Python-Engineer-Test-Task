from pydantic import BaseModel

class FriendCreate(BaseModel):
    name: str
    profession: str
    profession_description: str | None = None

class Friend(FriendCreate):
    id: str
    photo_url: str

    class Config:
        from_attributes = True