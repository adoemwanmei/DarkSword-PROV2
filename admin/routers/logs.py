from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from ..database import get_db, Log
from ..auth import get_current_user
from ..schemas import LogResponse, StatsResponse
from typing import Optional, List

router = APIRouter(prefix="/api/logs", tags=["logs"], redirect_slashes=False)


@router.get("", response_model=List[LogResponse])
async def get_logs(
    skip: int = 0,
    limit: int = 100,
    ip: Optional[str] = None,
    path: Optional[str] = None,
    log_type: Optional[str] = None,
    device_uuid: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Log).order_by(desc(Log.timestamp))
    
    if ip:
        query = query.filter(Log.ip.contains(ip))
    if path:
        query = query.filter(Log.path.contains(path))
    if log_type:
        query = query.filter(Log.log_type == log_type)
    if device_uuid:
        query = query.filter(Log.device_uuid == device_uuid)
    if start_time:
        query = query.filter(Log.timestamp >= start_time)
    if end_time:
        query = query.filter(Log.timestamp <= end_time)
    
    logs = query.offset(skip).limit(limit).all()
    return logs


@router.get("/stats", response_model=StatsResponse)
async def get_log_stats(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    total_requests = db.query(Log).count()
    total_devices = db.query(Log.ip).distinct().count()
    total_exfil = db.query(Log).filter(Log.log_type == "exfil").count()
    
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_requests = db.query(Log).filter(Log.timestamp >= today_start).count()
    today_exfil = db.query(Log).filter(and_(Log.log_type == "exfil", Log.timestamp >= today_start)).count()
    
    request_trend = []
    exfil_trend = []
    for i in range(7):
        date = today_start - timedelta(days=i)
        next_date = date + timedelta(days=1)
        count = db.query(Log).filter(and_(Log.timestamp >= date, Log.timestamp < next_date)).count()
        request_trend.insert(0, count)
        exfil_count = db.query(Log).filter(and_(
            Log.log_type == "exfil",
            Log.timestamp >= date,
            Log.timestamp < next_date
        )).count()
        exfil_trend.insert(0, exfil_count)
    
    return {
        "total_requests": total_requests,
        "total_devices": total_devices,
        "total_exfil": total_exfil,
        "today_requests": today_requests,
        "today_exfil": today_exfil,
        "request_trend": request_trend,
        "exfil_trend": exfil_trend
    }


@router.delete("/batch")
async def batch_delete_logs(log_ids: List[int], db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    deleted = db.query(Log).filter(Log.id.in_(log_ids)).delete(synchronize_session=False)
    db.commit()
    return {"message": f"Deleted {deleted} logs"}


@router.delete("/clear")
async def clear_logs(
    log_type: Optional[str] = None,
    device_uuid: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Log)
    if log_type:
        query = query.filter(Log.log_type == log_type)
    if device_uuid:
        query = query.filter(Log.device_uuid == device_uuid)
    deleted = query.delete(synchronize_session=False)
    db.commit()
    return {"message": f"Cleared {deleted} logs"}


@router.get("/{log_id}", response_model=LogResponse)
async def get_log(log_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log


@router.delete("/{log_id}")
async def delete_log(log_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    db.delete(log)
    db.commit()
    return {"message": "Log deleted"}
