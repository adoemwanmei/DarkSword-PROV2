from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db, User, create_audit_log
from ..auth import get_current_user, get_password_hash, requires_role
from ..schemas import UserResponse, UserCreate, UserUpdate
from .notifications import broadcast_notification_sync
from ..limiter import rate_limit
from typing import List

router = APIRouter(prefix="/api/users", tags=["users"], redirect_slashes=False)


@router.get("", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(requires_role("admin"))
):
    users = db.query(User).order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    return users


@rate_limit("10/minute")
@router.post("/", response_model=UserResponse)
async def create_user(
    request: Request,
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(requires_role("admin"))
):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    actor = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=actor, action="user_create", resource_type="user",
        resource_id=new_user.id, detail=f"Created user '{user.username}' with role '{user.role}'",
        ip_address=request.client.host if request.client else None
    )
    broadcast_notification_sync(
        db, title="新用户已创建", message=f"管理员 {actor} 创建了用户 {user.username}",
        category="user", related_resource_type="user", related_resource_id=new_user.id
    )
    return new_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(requires_role("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(requires_role("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_details = []
    if user_update.username:
        existing = db.query(User).filter(User.username == user_update.username, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        update_details.append(f"username: {user.username} -> {user_update.username}")
        user.username = user_update.username

    if user_update.password:
        user.password = get_password_hash(user_update.password)
        update_details.append("password updated")

    if user_update.role:
        update_details.append(f"role: {user.role} -> {user_update.role}")
        user.role = user_update.role

    db.commit()
    db.refresh(user)

    actor = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=actor, action="user_update", resource_type="user",
        resource_id=user_id, detail=f"Updated user {user_id}: {', '.join(update_details)}",
        ip_address=request.client.host if request.client else None
    )
    return user


@rate_limit("10/minute")
@router.delete("/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(requires_role("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == "admin" and user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    target_username = user.username
    db.delete(user)
    db.commit()

    actor = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=actor, action="user_delete", resource_type="user",
        resource_id=user_id, detail=f"Deleted user '{target_username}' (ID: {user_id})",
        ip_address=request.client.host if request.client else None
    )
    broadcast_notification_sync(
        db, title="用户已删除", message=f"管理员 {actor} 删除了用户 {target_username}",
        category="user", related_resource_type="user", related_resource_id=user_id
    )
    return {"message": "User deleted"}
