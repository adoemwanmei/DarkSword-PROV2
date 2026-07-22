from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db, Command, Device, create_audit_log
from ..auth import get_current_user
from ..schemas import CommandResponse, CommandCreate
from .notifications import broadcast_notification_sync
from datetime import datetime
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api/commands", tags=["commands"], redirect_slashes=False)

@router.post("", response_model=CommandResponse)
async def create_command(request: Request, command: CommandCreate, device_uuid: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    new_command = Command(device_uuid=device_uuid, command=command.command, status="pending")
    db.add(new_command)
    db.commit()
    db.refresh(new_command)
    device.last_command_time = datetime.now()
    db.commit()

    username = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=username, action="command_create", resource_type="command",
        resource_id=new_command.id, detail=f"Created command '{command.command}' for device {device_uuid}",
        ip_address=request.client.host if request.client else None
    )
    broadcast_notification_sync(
        db, title="新命令已创建", message=f"用户 {username} 向设备 {device_uuid} 发送了命令",
        category="command", related_device_uuid=device_uuid, related_resource_type="command",
        related_resource_id=new_command.id
    )
    return new_command

@router.get("")
async def get_commands(device_uuid: str = None, status: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Command).order_by(desc(Command.created_at))
    if device_uuid:
        query = query.filter(Command.device_uuid == device_uuid)
    if status:
        query = query.filter(Command.status == status)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "items": items}

@router.get("/{command_id}", response_model=CommandResponse)
async def get_command(command_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    command = db.query(Command).filter(Command.id == command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    return command

@router.put("/{command_id}/execute")
async def execute_command(command_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    command = db.query(Command).filter(Command.id == command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    command.status = "executing"
    db.commit()
    return {"message": "Command marked for execution"}

@router.put("/{command_id}/complete")
async def complete_command(command_id: int, output: str = "", db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    command = db.query(Command).filter(Command.id == command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    command.status = "completed"
    command.output = output
    command.executed_at = datetime.now()
    db.commit()
    return {"message": "Command completed"}

@router.post("/{command_id}/retry")
async def retry_command(command_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    command = db.query(Command).filter(Command.id == command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    if command.status == "pending":
        raise HTTPException(status_code=400, detail="Command is already pending")
    command.status = "pending"
    command.output = ""
    command.executed_at = None
    db.commit()
    return {"message": "Command retried"}


@router.delete("/{command_id}")
async def delete_command(request: Request, command_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    command = db.query(Command).filter(Command.id == command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    db.delete(command)
    db.commit()

    username = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=username, action="command_delete", resource_type="command",
        resource_id=command_id, detail=f"Deleted command {command_id}",
        ip_address=request.client.host if request.client else None
    )
    return {"message": "Command deleted"}


class BatchDeleteRequest(BaseModel):
    ids: List[int]


@router.delete("/batch")
async def batch_delete_commands(request: Request, delete_request: BatchDeleteRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not delete_request.ids:
        raise HTTPException(status_code=400, detail="No command IDs provided")
    deleted_count = db.query(Command).filter(Command.id.in_(delete_request.ids)).delete(synchronize_session=False)
    db.commit()

    username = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=username, action="command_batch_delete", resource_type="command",
        detail=f"Batch deleted {deleted_count} commands",
        ip_address=request.client.host if request.client else None
    )
    return {"message": f"Deleted {deleted_count} commands"}


@router.delete("/clear")
async def clear_commands(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    deleted_count = db.query(Command).delete(synchronize_session=False)
    db.commit()

    username = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=username, action="command_clear", resource_type="command",
        detail=f"Cleared all {deleted_count} commands",
        ip_address=request.client.host if request.client else None
    )
    return {"message": f"Cleared all {deleted_count} commands"}



