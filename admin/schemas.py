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


class ExfilDataResponse(BaseModel):
    id: int
    device_uuid: str
    category: str
    path: str
    description: Optional[str] = None
    file_path: str
    file_size: int
    uploaded_at: datetime


class StatsResponse(BaseModel):
    total_requests: int
    total_devices: int
    total_exfil: int
    today_requests: int
    today_exfil: int
    request_trend: List[int]
    exfil_trend: List[int]
