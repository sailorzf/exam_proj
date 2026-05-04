# backend/routers/settings.py
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import SystemSetting, User
from auth import require_admin
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/settings", tags=["settings"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

DEFAULT_SETTINGS = {
    "background_image": "",
    "copyright_text": "© 2026 智慧考试系统 版权所有",
}


class SettingValue(BaseModel):
    background_image: Optional[str] = ""
    copyright_text: Optional[str] = ""


@router.get("/")
def get_settings(db: Session = Depends(get_db)):
    settings = {s.key: s.value for s in db.query(SystemSetting).all()}
    for key, default in DEFAULT_SETTINGS.items():
        if key not in settings:
            settings[key] = default
    return settings


@router.put("/")
def update_settings(
    req: SettingValue,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    data = req.model_dump()
    for key, value in data.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            setting.value = value or ""
        else:
            setting = SystemSetting(key=key, value=value or "")
            db.add(setting)
    db.commit()
    return get_settings(db)


@router.post("/upload-image")
def upload_image(
    file: UploadFile = File(...),
    _admin: User = Depends(require_admin),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/WebP 格式")
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)
    return {"url": f"/api/uploads/{filename}"}
