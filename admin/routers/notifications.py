from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal, get_db
from ..auth import get_current_user

router = APIRouter()

@router.get("")
async def get_notifications(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return []

@router.put("/{id}/read")
async def mark_notification_read(id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"message": "Notification marked as read"}

@router.put("/read")
async def mark_all_read(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"message": "All notifications marked as read"}

@router.delete("")
async def clear_notifications(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"message": "All notifications cleared"}
