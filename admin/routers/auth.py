from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db, User, init_db, create_audit_log
from ..auth import authenticate_user, create_access_token, get_password_hash, get_current_user
from ..schemas import Token, UserResponse
from .. import config
from datetime import datetime

from ..limiter import rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"], redirect_slashes=False)

ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES


@rate_limit(config.AUTH_RATE_LIMIT)
@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    if not user:
        create_audit_log(
            db,
            username=form_data.username,
            action="login_failed",
            resource_type="auth",
            detail=f"Failed login attempt from IP {client_ip}",
            ip_address=client_ip,
            user_agent=user_agent
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.last_login = datetime.now()
    db.commit()

    create_audit_log(
        db,
        username=user.username,
        action="login_success",
        resource_type="auth",
        detail=f"User logged in from IP {client_ip}",
        ip_address=client_ip,
        user_agent=user_agent
    )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/init")
async def init_admin(db: Session = Depends(get_db)):
    init_db()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            password=get_password_hash("admin123"),
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return {"message": "Admin user created", "user": admin.username}
    return {"message": "Admin user already exists"}
