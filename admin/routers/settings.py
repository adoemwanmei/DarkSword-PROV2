from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import SessionLocal, get_db
from ..auth import get_current_user

router = APIRouter()

class C2Settings(BaseModel):
    c2_host: str = ''
    listen_host: str = '0.0.0.0'
    listen_port: int = 8080
    redirect_url: str = ''

class ExploitSettings(BaseModel):
    auto_exfil: bool = True
    exfil_categories: list = ['keychain', 'wifi', 'contacts']
    poll_interval: int = 30

@router.get("")
async def get_settings(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {
        "c2": {
            "c2_host": "",
            "listen_host": "0.0.0.0",
            "listen_port": 8080,
            "redirect_url": ""
        },
        "exploit": {
            "auto_exfil": True,
            "exfil_categories": ["keychain", "wifi", "contacts"],
            "poll_interval": 30
        }
    }

@router.put("/c2")
async def update_c2_settings(settings: C2Settings, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"message": "C2 settings updated", "data": settings.dict()}

@router.put("/exploit")
async def update_exploit_settings(settings: ExploitSettings, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"message": "Exploit settings updated", "data": settings.dict()}
