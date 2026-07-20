from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db, Command, Device
from ..auth import get_current_user
from ..schemas import CommandResponse, CommandCreate
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/commands", tags=["commands"], redirect_slashes=False)

@router.post("", response_model=CommandResponse)
async def create_command(command: CommandCreate, device_uuid: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    new_command = Command(device_uuid=device_uuid, command=command.command, status="pending")
    db.add(new_command)
    db.commit()
    db.refresh(new_command)
    device.last_command_time = datetime.now()
    db.commit()
    return new_command

@router.get("", response_model=List[CommandResponse])
async def get_commands(device_uuid: str = None, status: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Command).order_by(desc(Command.created_at))
    if device_uuid:
        query = query.filter(Command.device_uuid == device_uuid)
    if status:
        query = query.filter(Command.status == status)
    return query.offset(skip).limit(limit).all()

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

@router.delete("/{command_id}")
async def delete_command(command_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    command = db.query(Command).filter(Command.id == command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    db.delete(command)
    db.commit()
    return {"message": "Command deleted"}
