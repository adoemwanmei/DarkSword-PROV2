from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import Optional

from ..database import get_db, AuditLog
from ..auth import get_current_user

router = APIRouter(prefix="/api/audit", tags=["audit"], redirect_slashes=False)


@router.get("")
async def get_audit_logs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    username: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(AuditLog).order_by(desc(AuditLog.timestamp))

    if username:
        query = query.filter(AuditLog.username.contains(username))
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_time:
        query = query.filter(AuditLog.timestamp >= start_time)
    if end_time:
        query = query.filter(AuditLog.timestamp <= end_time)

    total = query.count()
    logs = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": logs,
        "skip": skip,
        "limit": limit
    }


@router.get("/stats")
async def get_audit_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    total = db.query(func.count(AuditLog.id)).scalar()

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(func.count(AuditLog.id)).filter(AuditLog.timestamp >= today_start).scalar()

    action_stats = db.query(
        AuditLog.action,
        func.count(AuditLog.id)
    ).group_by(AuditLog.action).all()

    user_stats = db.query(
        AuditLog.username,
        func.count(AuditLog.id)
    ).group_by(AuditLog.username).order_by(desc(func.count(AuditLog.id))).limit(10).all()

    return {
        "total": total,
        "today": today_count,
        "by_action": dict(action_stats),
        "by_user": dict(user_stats)
    }
