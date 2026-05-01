# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import LoginRequest, LoginResponse, RegisterRequest
from auth import hash_password, verify_password, create_token, require_teacher

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_token(user.id, user.role, user.username)
    return LoginResponse(token=token, role=user.role, username=user.username)


@router.post("/register")
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db),
    _teacher: User = Depends(require_teacher),
):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    if req.role not in ("teacher", "student"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    user = User(username=req.username, password_hash=hash_password(req.password), role=req.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role}
