import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserCreate, UserUpdate, UserResponse, UserImportResponse
from auth import hash_password, require_admin

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
def list_users(role: str | None = None, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    return q.order_by(User.id).all()


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(req: UserCreate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    if req.role not in ("teacher", "student"):
        raise HTTPException(status_code=400, detail="Invalid role")
    user = User(username=req.username, password_hash=hash_password(req.password), role=req.role,
                name=req.name, gender=req.gender, phone=req.phone, class_name=req.class_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, req: UserUpdate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if req.role and req.role not in ("teacher", "student"):
        raise HTTPException(status_code=400, detail="Invalid role")
    for field, value in req.model_dump(exclude_unset=True).items():
        if field == "password":
            setattr(user, field, hash_password(value))
        else:
            setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot delete admin account")
    db.delete(user)
    db.commit()


@router.get("/template")
def download_template(_admin: User = Depends(require_admin)):
    template = "username,password,role,name,gender,phone,class_name\nzhangsan,pass123,student,张三,男,13800000001,一班\n"
    return StreamingResponse(
        iter([template.encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=user_template.csv"},
    )


@router.post("/import", response_model=UserImportResponse)
def import_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    errors = []
    imported = 0
    for i, row in enumerate(reader, start=1):
        try:
            username = row.get("username", "").strip()
            password = row.get("password", "").strip()
            role = row.get("role", "").strip()
            name = row.get("name", "").strip() or None
            gender = row.get("gender", "").strip() or None
            phone = row.get("phone", "").strip() or None
            class_name = row.get("class_name", "").strip() or None
            if not username or not password:
                errors.append(f"Row {i}: username and password are required")
                continue
            if role not in ("teacher", "student"):
                errors.append(f"Row {i}: invalid role '{role}'")
                continue
            if db.query(User).filter(User.username == username).first():
                errors.append(f"Row {i}: username '{username}' already exists")
                continue
            user = User(username=username, password_hash=hash_password(password), role=role,
                        name=name, gender=gender, phone=phone, class_name=class_name)
            db.add(user)
            imported += 1
        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")
    db.commit()
    return UserImportResponse(imported=imported, errors=errors)
