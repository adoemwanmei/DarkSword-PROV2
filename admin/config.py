"""DarkSword Admin 配置加载模块.

支持从 .env 文件加载环境变量，提供统一配置入口.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent

# 加载 .env 文件（如果 python-dotenv 已安装）
if load_dotenv is not None:
    dotenv_path = BASE_DIR / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)


# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "darksword_secret_key_change_me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# CORS 配置
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "")
if CORS_ORIGINS_STR:
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",") if origin.strip()]
else:
    # 开发环境默认
    CORS_ORIGINS = ["http://localhost:8080", "http://localhost:5173", "http://localhost:3000"]

# 限流配置
RATE_LIMIT = os.getenv("RATE_LIMIT", "100/minute")
AUTH_RATE_LIMIT = os.getenv("AUTH_RATE_LIMIT", "5/minute")
