from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db, User, init_db
from ..auth import authenticate_user, create_access_token, get_password_hash, get_current_user
from ..schemas import Token, UserResponse
from datetime import datetime

router = APIRouter(prefix="/api/auth", tags=["auth"], redirect_slashes=False)

ACCESS_TOKEN_EXPIRE_MINUTES = 30


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.last_login = datetime.now()
    db.commit()
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
