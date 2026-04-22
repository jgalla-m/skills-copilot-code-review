from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from ..database import announcements_collection
from .auth import get_current_user

class Announcement(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str
    message: str
    start_date: Optional[str] = None
    expiration_date: str
    created_by: str
    created_at: str

class AnnouncementCreate(BaseModel):
    title: str
    message: str
    start_date: Optional[str] = None
    expiration_date: str

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    start_date: Optional[str] = None
    expiration_date: Optional[str] = None

router = APIRouter(prefix="/announcements", tags=["announcements"])

@router.get("/", response_model=List[Announcement])
def list_announcements():
    now = datetime.utcnow().isoformat()
    anns = list(announcements_collection.find({
        "$or": [
            {"expiration_date": {"$gte": now}},
            {"expiration_date": None}
        ]
    }))
    return anns

@router.post("/", response_model=Announcement, status_code=status.HTTP_201_CREATED)
def create_announcement(data: AnnouncementCreate, user=Depends(get_current_user)):
    ann = data.dict()
    ann["created_by"] = user["username"]
    ann["created_at"] = datetime.utcnow().isoformat()
    result = announcements_collection.insert_one(ann)
    ann["_id"] = str(result.inserted_id)
    return ann

@router.put("/{announcement_id}", response_model=Announcement)
def update_announcement(announcement_id: str, data: AnnouncementUpdate, user=Depends(get_current_user)):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update.")
    result = announcements_collection.find_one_and_update(
        {"_id": announcement_id},
        {"$set": update_data},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    return result

@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(announcement_id: str, user=Depends(get_current_user)):
    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    return None
