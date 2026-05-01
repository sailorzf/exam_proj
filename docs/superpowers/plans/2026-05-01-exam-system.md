# Exam System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight online exam system with teacher exam management and student exam-taking interfaces.

**Architecture:** FastAPI monolith serving both REST API and static Vue SPA files, backed by SQLite via SQLAlchemy.

**Tech Stack:** Python FastAPI, SQLAlchemy, SQLite, bcrypt, PyJWT, Vue 3, Vite, Vue Router, Axios

---

## File Map

### Backend files (all new)
| File | Responsibility |
|---|---|
| `backend/config.py` | App config: DB path, JWT secret, expiry |
| `backend/database.py` | SQLAlchemy engine, session factory, init_db |
| `backend/models.py` | All 6 ORM models |
| `backend/schemas.py` | All Pydantic request/response schemas |
| `backend/auth.py` | JWT creation, verification, password hashing, role dependency |
| `backend/routers/auth.py` | Login + register endpoints |
| `backend/routers/questions.py` | Question CRUD + text import |
| `backend/routers/papers.py` | Paper CRUD + build + publish/unpublish |
| `backend/routers/exams.py` | Exam session, question delivery, answer saving, submission |
| `backend/routers/grading.py` | Submission review, essay scoring, publish results |
| `backend/services/question_parser.py` | Text file to Question list parser |
| `backend/services/exam_engine.py` | Paper building (random/specified selection) |
| `backend/services/grading_engine.py` | Auto-grading logic |
| `backend/main.py` | FastAPI app, router mounting, static file serving |
| `backend/requirements.txt` | Python dependencies |

### Frontend files (all new)
| File | Responsibility |
|---|---|
| `frontend/package.json` | Vue 3 dependencies |
| `frontend/vite.config.js` | Vite build config |
| `frontend/index.html` | HTML entry |
| `frontend/src/main.js` | Vue app entry |
| `frontend/src/router.js` | Vue Router with role-based guards |
| `frontend/src/api.js` | Axios instance + API methods |
| `frontend/src/auth.js` | JWT storage, login state, role checks |
| `frontend/src/views/Login.vue` | Login page |
| `frontend/src/views/student/ExamList.vue` | Available exams list |
| `frontend/src/views/student/ExamView.vue` | Exam-taking interface |
| `frontend/src/views/student/Results.vue` | Results list + detail |
| `frontend/src/views/teacher/QuestionBank.vue` | Question management |
| `frontend/src/views/teacher/PaperBuilder.vue` | Paper creation + question selection |
| `frontend/src/views/teacher/ExamManager.vue` | Publish/unpublish exams |
| `frontend/src/views/teacher/Submissions.vue` | View submissions + grade essays |
| `frontend/src/views/teacher/Grades.vue` | Score table |
| `frontend/src/components/QuestionRenderer.vue` | Type-aware question input rendering |
| `frontend/src/components/Timer.vue` | Countdown timer |
| `frontend/src/components/NavBar.vue` | Role-aware navigation |

---

### Task 1: Project scaffolding and config

**Files:**
- Create: `backend/config.py`
- Create: `backend/requirements.txt`

- [ ] **Step 1: Create config.py**

```python
# backend/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'exam.db'}"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 8
```

- [ ] **Step 2: Create requirements.txt**

```
fastapi==0.115.6
uvicorn==0.34.0
sqlalchemy==2.0.36
pydantic==2.10.3
bcrypt==4.2.1
PyJWT==2.10.1
```

- [ ] **Step 3: Create data directory**

```bash
mkdir -p data
```

---

### Task 2: Database models

**Files:**
- Create: `backend/database.py`
- Create: `backend/models.py`

- [ ] **Step 1: Create database.py**

```python
# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = DeclarativeBase()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 2: Create models.py**

```python
# backend/models.py
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    papers = relationship("Paper", back_populates="creator")
    questions = relationship("Question", back_populates="creator")
    sessions = relationship("ExamSession", back_populates="student")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(String, nullable=True)
    answer_text = Column(Text, nullable=False)
    points = Column(Integer, default=5)
    category = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    creator = relationship("User", back_populates="questions")
    paper_questions = relationship("PaperQuestion", back_populates="question")
    answers = relationship("Answer", back_populates="question")


class Paper(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, nullable=False, default="draft")
    window_start = Column(DateTime, nullable=True)
    window_end = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    creator = relationship("User", back_populates="papers")
    paper_questions = relationship("PaperQuestion", back_populates="paper", cascade="all, delete-orphan")
    sessions = relationship("ExamSession", back_populates="paper")


class PaperQuestion(Base):
    __tablename__ = "paper_questions"
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    order_index = Column(Integer, nullable=False)
    custom_points = Column(Integer, nullable=True)
    paper = relationship("Paper", back_populates="paper_questions")
    question = relationship("Question", back_populates="paper_questions")
    answers = relationship("Answer", back_populates="paper_question")


class ExamSession(Base):
    __tablename__ = "exam_sessions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    submit_time = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="in_progress")
    auto_score = Column(Float, nullable=True)
    manual_score = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)
    student = relationship("User", back_populates="sessions")
    paper = relationship("Paper", back_populates="sessions")
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("exam_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    paper_question_id = Column(Integer, ForeignKey("paper_questions.id"), nullable=True)
    student_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=True)
    score = Column(Float, nullable=True)
    teacher_comment = Column(Text, nullable=True)
    session = relationship("ExamSession", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    paper_question = relationship("PaperQuestion", back_populates="answers")
```

- [ ] **Step 3: Verify imports**

```bash
cd backend && python -c "from models import Base, User, Question, Paper, PaperQuestion, ExamSession, Answer; print('OK')"
```

---

### Task 3: Pydantic schemas

**Files:**
- Create: `backend/schemas.py`

- [ ] **Step 1: Create schemas.py**

```python
# backend/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str


class QuestionCreate(BaseModel):
    type: str
    question_text: str
    options: Optional[List[str]] = None
    answer_text: str
    points: int = 5
    category: Optional[str] = None


class QuestionUpdate(BaseModel):
    type: Optional[str] = None
    question_text: Optional[str] = None
    options: Optional[List[str]] = None
    answer_text: Optional[str] = None
    points: Optional[int] = None
    category: Optional[str] = None


class QuestionResponse(BaseModel):
    id: int
    type: str
    question_text: str
    options: Optional[List[str]] = None
    answer_text: str
    points: int
    category: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True


class ImportRequest(BaseModel):
    file_text: str


class ImportResponse(BaseModel):
    imported: int
    errors: List[str] = []


class PaperCreate(BaseModel):
    title: str
    description: Optional[str] = None


class PaperUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class PaperPublishRequest(BaseModel):
    window_start: datetime
    window_end: datetime
    duration_minutes: int


class BuildSpecifiedRequest(BaseModel):
    question_ids: List[int]


class BuildRandomRequest(BaseModel):
    strategy: str = "random"
    count: int
    tags: Optional[List[str]] = None


class PaperQuestionResponse(BaseModel):
    id: int
    paper_id: int
    question_id: int
    order_index: int
    custom_points: Optional[int] = None
    class Config:
        from_attributes = True


class PaperResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True


class StartExamRequest(BaseModel):
    paper_id: int


class SaveAnswerRequest(BaseModel):
    question_id: int
    answer: str


class ExamQuestionItem(BaseModel):
    index: int
    question_id: int
    type: str
    question_text: str
    options: Optional[List[str]] = None
    points: int


class ExamSessionResponse(BaseModel):
    id: int
    student_id: int
    paper_id: int
    start_time: datetime
    submit_time: Optional[datetime] = None
    status: str
    auto_score: Optional[float] = None
    manual_score: Optional[float] = None
    total_score: Optional[float] = None
    class Config:
        from_attributes = True


class EssayScoreRequest(BaseModel):
    score: float
    comment: Optional[str] = None


class AnswerDetail(BaseModel):
    id: int
    question_id: int
    question_text: str
    question_type: str
    student_answer: str
    correct_answer: str
    is_correct: Optional[bool]
    score: Optional[float]
    points: int
    teacher_comment: Optional[str] = None


class SubmissionDetail(BaseModel):
    session: ExamSessionResponse
    answers: List[AnswerDetail]


class SubmissionListItem(BaseModel):
    session_id: int
    student_username: str
    status: str
    auto_score: Optional[float]
    manual_score: Optional[float]
    total_score: Optional[float]
    submit_time: Optional[datetime]


class ResultListItem(BaseModel):
    session_id: int
    paper_title: str
    total_score: Optional[float]
    status: str
    published_at: Optional[datetime] = None
```

- [ ] **Step 2: Verify import**

```bash
cd backend && python -c "from schemas import *; print('OK')"
```

---

### Task 4: Auth module

**Files:**
- Create: `backend/auth.py`

- [ ] **Step 1: Create auth.py**

```python
# backend/auth.py
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User
from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_token(user_id: int, role: str, username: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": user_id, "role": role, "username": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_teacher(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher access required")
    return current_user


def require_student(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access required")
    return current_user
```

- [ ] **Step 2: Test auth functions**

```bash
cd backend && python -c "
from auth import hash_password, verify_password
h = hash_password('test123')
assert verify_password('test123', h) == True
assert verify_password('wrong', h) == False
print('OK')
"
```

---

### Task 5: Auth router (login + register)

**Files:**
- Create: `backend/routers/__init__.py`
- Create: `backend/routers/auth.py`
- Create: `backend/main.py` (minimal)

- [ ] **Step 1: Create routers/__init__.py** (empty)

```bash
touch backend/routers/__init__.py
```

- [ ] **Step 2: Create routers/auth.py**

```python
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
```

- [ ] **Step 3: Create minimal main.py**

```python
# backend/main.py
from fastapi import FastAPI
from database import init_db
from routers import auth as auth_router

app = FastAPI()
app.include_router(auth_router.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Test**

```bash
cd backend && uvicorn main:app --port 8000 &
curl -X POST http://localhost:8000/api/login -H "Content-Type: application/json" -d '{"username":"teacher1","password":"pass123"}'
pkill -f "uvicorn main:app"
```

---

### Task 6: Question parser service

**Files:**
- Create: `backend/services/__init__.py`
- Create: `backend/services/question_parser.py`

- [ ] **Step 1: Create services/__init__.py** (empty)

- [ ] **Step 2: Create question_parser.py**

```python
# backend/services/question_parser.py
import re
from typing import List, Dict, Any


def parse_questions(text: str) -> List[Dict[str, Any]]:
    blocks = re.split(r'\n(?=Q\d+[\.\)]\s)', text.strip())
    blocks = [b.strip() for b in blocks if b.strip()]
    questions = []
    for block in blocks:
        q = _parse_block(block)
        if q:
            questions.append(q)
    return questions


def _parse_block(block: str) -> Dict[str, Any] | None:
    lines = block.split('\n')
    if not lines:
        return None

    first_line = lines[0]
    question_text = re.sub(r'^Q\d+[\.\)]\s*', '', first_line).strip()

    option_lines = []
    answer_line_idx = None
    other_lines = []

    for i, line in enumerate(lines[1:], start=1):
        line = line.strip()
        if re.match(r'^[A-Z][\.\)]\s', line):
            option_lines.append(line)
        elif re.match(r'^(A:|答案:)', line):
            answer_line_idx = i
            break
        else:
            other_lines.append(line)

    answer_text = ""
    if answer_line_idx is not None:
        answer_text = lines[answer_line_idx]
        answer_text = re.sub(r'^(A:|答案:)\s*', '', answer_text).strip()
    elif other_lines:
        answer_text = ' '.join(other_lines).strip()

    if not answer_text:
        return None

    if option_lines:
        options = [re.sub(r'^[A-Z][\.\)]\s*', '', opt).strip() for opt in option_lines]
        qtype = "choice_multi" if "(多选)" in question_text else "choice_single"
        return {"type": qtype, "question_text": question_text, "options": options, "answer_text": answer_text}
    elif "___" in question_text or "____" in question_text:
        return {"type": "fill_blank", "question_text": question_text, "options": None, "answer_text": answer_text}
    else:
        return {"type": "essay", "question_text": question_text, "options": None, "answer_text": answer_text}
```

- [ ] **Step 3: Test parser**

```bash
cd backend && python -c "
from services.question_parser import parse_questions
sample = '''Q1. 哪个正确？
A. 选项一
B. 选项二
A: A

Q2. 填空：___
A: 答案

Q3. 简述。
A: 简答内容

Q4. 哪些是金属？（多选）
A. 铁
B. 氧
C. 铜
A: A,C
'''
qs = parse_questions(sample)
assert len(qs) == 4
assert qs[0]['type'] == 'choice_single'
assert qs[1]['type'] == 'fill_blank'
assert qs[2]['type'] == 'essay'
assert qs[3]['type'] == 'choice_multi'
print('All parser tests passed')
"
```

---

### Task 7: QuestionBank router

**Files:**
- Create: `backend/routers/questions.py`

- [ ] **Step 1: Create routers/questions.py**

```python
# backend/routers/questions.py
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, Question
from schemas import QuestionCreate, QuestionUpdate, QuestionResponse, ImportRequest, ImportResponse
from auth import require_teacher
from services.question_parser import parse_questions

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.get("/", response_model=list[QuestionResponse])
def list_questions(category: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Question)
    if category:
        q = q.filter(Question.category == category)
    return q.order_by(Question.id.desc()).all()


@router.post("/", response_model=QuestionResponse, status_code=201)
def create_question(req: QuestionCreate, db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    q = Question(
        type=req.type, question_text=req.question_text,
        options=json.dumps(req.options) if req.options else None,
        answer_text=req.answer_text, points=req.points,
        category=req.category, created_by=teacher.id,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


@router.put("/{question_id}", response_model=QuestionResponse)
def update_question(question_id: int, req: QuestionUpdate, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        if field == "options":
            setattr(q, field, json.dumps(value) if value else None)
        else:
            setattr(q, field, value)
    db.commit()
    db.refresh(q)
    return q


@router.delete("/{question_id}", status_code=204)
def delete_question(question_id: int, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()


@router.post("/import", response_model=ImportResponse)
def import_questions(req: ImportRequest, db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    parsed = parse_questions(req.file_text)
    errors = []
    created = 0
    for i, item in enumerate(parsed):
        try:
            q = Question(
                type=item["type"], question_text=item["question_text"],
                options=json.dumps(item["options"]) if item.get("options") else None,
                answer_text=item["answer_text"], points=5, created_by=teacher.id,
            )
            db.add(q)
            created += 1
        except Exception as e:
            errors.append(f"Question {i+1}: {str(e)}")
    db.commit()
    return ImportResponse(imported=created, errors=errors)
```

- [ ] **Step 2: Update main.py** — add `from routers import questions as questions_router` and `app.include_router(questions_router.router)`

---

### Task 8: Exam engine service

**Files:**
- Create: `backend/services/exam_engine.py`

- [ ] **Step 1: Create exam_engine.py**

```python
# backend/services/exam_engine.py
import random
from sqlalchemy.orm import Session
from models import Paper, PaperQuestion, Question


def build_paper_specified(db: Session, paper: Paper, question_ids: list[int]) -> list[PaperQuestion]:
    existing = db.query(PaperQuestion).filter(PaperQuestion.paper_id == paper.id).count()
    result = []
    for idx, qid in enumerate(question_ids, start=existing + 1):
        q = db.query(Question).filter(Question.id == qid).first()
        if not q:
            continue
        pq = PaperQuestion(paper_id=paper.id, question_id=qid, order_index=idx)
        db.add(pq)
        result.append(pq)
    db.flush()
    return result


def build_paper_random(db: Session, paper: Paper, count: int, tags: list[str] | None = None) -> list[PaperQuestion]:
    q = db.query(Question)
    if tags:
        q = q.filter(Question.category.in_(tags))
    all_q = q.all()
    if not all_q:
        return []
    selected = random.sample(all_q, min(count, len(all_q)))
    existing = db.query(PaperQuestion).filter(PaperQuestion.paper_id == paper.id).count()
    result = []
    for idx, question in enumerate(selected, start=existing + 1):
        pq = PaperQuestion(paper_id=paper.id, question_id=question.id, order_index=idx)
        db.add(pq)
        result.append(pq)
    db.flush()
    return result
```

---

### Task 9: PaperBuilder router

**Files:**
- Create: `backend/routers/papers.py`

- [ ] **Step 1: Create routers/papers.py**

```python
# backend/routers/papers.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Paper, PaperQuestion, Question
from schemas import PaperCreate, PaperUpdate, PaperResponse, PaperQuestionResponse, BuildSpecifiedRequest, BuildRandomRequest, PaperPublishRequest
from auth import require_teacher
from services.exam_engine import build_paper_specified, build_paper_random

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.get("/", response_model=list[PaperResponse])
def list_papers(db: Session = Depends(get_db)):
    return db.query(Paper).order_by(Paper.id.desc()).all()


@router.post("/", response_model=PaperResponse, status_code=201)
def create_paper(req: PaperCreate, db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    p = Paper(title=req.title, description=req.description, created_by=teacher.id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    p = db.query(Paper).filter(Paper.id == paper_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    return p


@router.get("/{paper_id}/questions", response_model=list[PaperQuestionResponse])
def get_paper_questions(paper_id: int, db: Session = Depends(get_db)):
    p = db.query(Paper).filter(Paper.id == paper_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    return db.query(PaperQuestion).filter(PaperQuestion.paper_id == paper_id).order_by(PaperQuestion.order_index).all()


@router.put("/{paper_id}", response_model=PaperResponse)
def update_paper(paper_id: int, req: PaperUpdate, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    p = db.query(Paper).filter(Paper.id == paper_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{paper_id}", status_code=204)
def delete_paper(paper_id: int, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    p = db.query(Paper).filter(Paper.id == paper_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    if p.status != "draft":
        raise HTTPException(status_code=400, detail="Cannot delete non-draft paper")
    db.delete(p)
    db.commit()


@router.post("/{paper_id}/build")
def build_paper(paper_id: int, req: BuildSpecifiedRequest | BuildRandomRequest, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    p = db.query(Paper).filter(Paper.id == paper_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    if p.status != "draft":
        raise HTTPException(status_code=400, detail="Cannot modify non-draft paper")
    if hasattr(req, "question_ids"):
        items = build_paper_specified(db, p, req.question_ids)
    else:
        items = build_paper_random(db, p, req.count, req.tags)
    db.commit()
    return {"added": len(items)}


@router.post("/{paper_id}/publish")
def publish_paper(paper_id: int, req: PaperPublishRequest, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    p = db.query(Paper).filter(Paper.id == paper_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    qc = db.query(PaperQuestion).filter(PaperQuestion.paper_id == paper_id).count()
    if qc == 0:
        raise HTTPException(status_code=400, detail="Paper has no questions")
    p.status = "active"
    p.window_start = req.window_start
    p.window_end = req.window_end
    p.duration_minutes = req.duration_minutes
    db.commit()
    db.refresh(p)
    return p


@router.put("/{paper_id}/unpublish")
def unpublish_paper(paper_id: int, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    p = db.query(Paper).filter(Paper.id == paper_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    p.status = "offline"
    db.commit()
    db.refresh(p)
    return p
```

- [ ] **Step 2: Update main.py** — add `from routers import papers as papers_router` and `app.include_router(papers_router.router)`

---

### Task 10: Grading engine service

**Files:**
- Create: `backend/services/grading_engine.py`

- [ ] **Step 1: Create grading_engine.py**

```python
# backend/services/grading_engine.py
import re
from sqlalchemy.orm import Session
from models import Answer, Question, ExamSession


def normalize_fill_blank(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r'[，,、；;。.\s]+', '', text)
    return text


def grade_submission(db: Session, session: ExamSession) -> dict:
    answers = db.query(Answer).filter(Answer.session_id == session.id).all()
    auto_score = 0.0
    graded_count = 0

    for answer in answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if not question:
            continue

        pts = answer.paper_question.custom_points if answer.paper_question else question.points

        if question.type == "choice_single":
            correct = answer.student_answer.strip() == question.answer_text.strip()
            answer.is_correct = correct
            answer.score = pts if correct else 0
            if correct:
                auto_score += pts
            graded_count += 1

        elif question.type == "choice_multi":
            student_set = set(a.strip() for a in answer.student_answer.replace(" ", "").split(",") if a.strip())
            correct_set = set(a.strip() for a in question.answer_text.replace(" ", "").split(",") if a.strip())
            correct = student_set == correct_set
            answer.is_correct = correct
            answer.score = pts if correct else 0
            if correct:
                auto_score += pts
            graded_count += 1

        elif question.type == "fill_blank":
            correct = normalize_fill_blank(answer.student_answer) == normalize_fill_blank(question.answer_text)
            answer.is_correct = correct
            answer.score = pts if correct else 0
            if correct:
                auto_score += pts
            graded_count += 1

    session.auto_score = auto_score
    session.status = "submitted"
    db.flush()
    return {"auto_score": auto_score, "total_questions": len(answers), "graded_count": graded_count}
```

- [ ] **Step 2: Test grading**

```bash
cd backend && python -c "
from services.grading_engine import normalize_fill_blank
assert normalize_fill_blank(' 亚洲 ') == normalize_fill_blank('亚洲')
assert normalize_fill_blank('亚洲') == normalize_fill_blank('亚 洲')
print('OK')
"
```

---

### Task 11: ExamRunner router

**Files:**
- Create: `backend/routers/exams.py`

- [ ] **Step 1: Create routers/exams.py**

```python
# backend/routers/exams.py
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Paper, PaperQuestion, Question, ExamSession, Answer
from schemas import StartExamRequest, SaveAnswerRequest, ExamSessionResponse
from auth import require_student
from services.grading_engine import grade_submission

router = APIRouter(prefix="/api/exams", tags=["exams"])


@router.get("/available")
def list_available_exams(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    papers = db.query(Paper).filter(
        Paper.status == "active",
        Paper.window_start <= now,
        Paper.window_end >= now,
    ).all()
    result = []
    for p in papers:
        qc = db.query(PaperQuestion).filter(PaperQuestion.paper_id == p.id).count()
        result.append({"id": p.id, "title": p.title, "description": p.description,
                       "duration_minutes": p.duration_minutes, "window_start": p.window_start,
                       "window_end": p.window_end, "question_count": qc})
    return result


@router.post("/start")
def start_exam(req: StartExamRequest, db: Session = Depends(get_db), student: User = Depends(require_student)):
    paper = db.query(Paper).filter(Paper.id == req.paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if paper.status != "active":
        raise HTTPException(status_code=400, detail="Exam not active")
    now = datetime.utcnow()
    if paper.window_start and now < paper.window_start:
        raise HTTPException(status_code=400, detail="Exam not yet open")
    if paper.window_end and now > paper.window_end:
        raise HTTPException(status_code=400, detail="Exam has closed")

    existing = db.query(ExamSession).filter(
        ExamSession.student_id == student.id, ExamSession.paper_id == paper.id,
        ExamSession.status == "in_progress").first()
    if existing:
        return ExamSessionResponse.model_validate(existing)

    session = ExamSession(student_id=student.id, paper_id=paper.id, start_time=now)
    db.add(session)
    db.commit()
    db.refresh(session)
    return ExamSessionResponse.model_validate(session)


@router.get("/{session_id}/questions")
def get_exam_questions(session_id: int, db: Session = Depends(get_db), student: User = Depends(require_student)):
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session or session.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not your exam")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Exam not in progress")
    pqs = db.query(PaperQuestion).filter(PaperQuestion.paper_id == session.paper_id).order_by(PaperQuestion.order_index).all()
    result = []
    for idx, pq in enumerate(pqs):
        q = db.query(Question).filter(Question.id == pq.question_id).first()
        result.append({"index": idx, "question_id": q.id, "type": q.type,
                       "question_text": q.question_text,
                       "options": json.loads(q.options) if q.options else None,
                       "points": pq.custom_points or q.points})
    return result


@router.put("/{session_id}/answer")
def save_answer(session_id: int, req: SaveAnswerRequest, db: Session = Depends(get_db), student: User = Depends(require_student)):
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session or session.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not your exam")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Exam not in progress")

    pq = db.query(PaperQuestion).filter(PaperQuestion.paper_id == session.paper_id,
                                         PaperQuestion.question_id == req.question_id).first()
    answer = db.query(Answer).filter(Answer.session_id == session_id, Answer.question_id == req.question_id).first()
    if answer:
        answer.student_answer = req.answer
    else:
        answer = Answer(session_id=session_id, question_id=req.question_id,
                        paper_question_id=pq.id if pq else None, student_answer=req.answer)
        db.add(answer)
    db.commit()
    return {"saved": True}


@router.post("/{session_id}/submit")
def submit_exam(session_id: int, db: Session = Depends(get_db), student: User = Depends(require_student)):
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session or session.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not your exam")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Exam already submitted")
    session.submit_time = datetime.utcnow()
    result = grade_submission(db, session)
    db.commit()
    db.refresh(session)
    return {"session": ExamSessionResponse.model_validate(session), "grading": result}
```

- [ ] **Step 2: Update main.py** — add `from routers import exams as exams_router` and `app.include_router(exams_router.router)`

---

### Task 12: Grading router

**Files:**
- Create: `backend/routers/grading.py`

- [ ] **Step 1: Create routers/grading.py**

```python
# backend/routers/grading.py
import json
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import User, ExamSession, Answer, Question, Paper
from schemas import EssayScoreRequest, SubmissionDetail, SubmissionListItem, AnswerDetail, ExamSessionResponse, ResultListItem
from auth import require_teacher, require_student

router = APIRouter(prefix="/api", tags=["grading"])


@router.get("/submissions", response_model=list[SubmissionListItem])
def list_submissions(paper_id: int | None = None, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    q = db.query(ExamSession)
    if paper_id:
        q = q.filter(ExamSession.paper_id == paper_id)
    sessions = q.all()
    result = []
    for s in sessions:
        student = db.query(User).filter(User.id == s.student_id).first()
        essay_scores = db.query(Answer).filter(Answer.session_id == s.id, Answer.score.isnot(None)).all()
        manual = sum(a.score or 0 for a in essay_scores)
        s.manual_score = manual if manual > 0 else s.manual_score
        s.total_score = (s.auto_score or 0) + (s.manual_score or 0)
        paper = db.query(Paper).filter(Paper.id == s.paper_id).first()
        result.append(SubmissionListItem(
            session_id=s.id, student_username=student.username if student else "Unknown",
            status=s.status, auto_score=s.auto_score, manual_score=s.manual_score,
            total_score=s.total_score, submit_time=s.submit_time))
    return result


@router.get("/submissions/{session_id}/detail", response_model=SubmissionDetail)
def get_submission_detail(session_id: int, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Submission not found")
    answers = db.query(Answer).filter(Answer.session_id == session_id).all()
    answer_details = []
    for a in answers:
        q = db.query(Question).filter(Question.id == a.question_id).first()
        pts = a.paper_question.custom_points if a.paper_question else q.points
        answer_details.append(AnswerDetail(
            id=a.id, question_id=q.id, question_text=q.question_text, question_type=q.type,
            student_answer=a.student_answer, correct_answer=q.answer_text,
            is_correct=a.is_correct, score=a.score, points=pts, teacher_comment=a.teacher_comment))
    return SubmissionDetail(session=ExamSessionResponse.model_validate(session), answers=answer_details)


@router.post("/answers/{answer_id}/score")
def score_answer(answer_id: int, req: EssayScoreRequest, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    answer.score = req.score
    answer.teacher_comment = req.comment
    db.commit()
    session = db.query(ExamSession).filter(ExamSession.id == answer.session_id).first()
    if session:
        essay_total = db.query(Answer).filter(Answer.session_id == session.id, Answer.score.isnot(None)).with_entities(db.func.sum(Answer.score)).scalar()
        session.manual_score = essay_total or 0
        session.total_score = (session.auto_score or 0) + (session.manual_score or 0)
        db.commit()
    return {"scored": True}


@router.post("/submissions/{session_id}/publish")
def publish_submission(session_id: int, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Submission not found")
    essay_total = db.query(Answer).filter(Answer.session_id == session_id, Answer.score.isnot(None)).with_entities(db.func.sum(Answer.score)).scalar()
    session.manual_score = essay_total or 0
    session.total_score = (session.auto_score or 0) + (session.manual_score or 0)
    session.status = "published"
    db.commit()
    db.refresh(session)
    return ExamSessionResponse.model_validate(session)


@router.get("/results", response_model=list[ResultListItem])
def list_results(db: Session = Depends(get_db), student: User = Depends(require_student)):
    sessions = db.query(ExamSession).filter(ExamSession.student_id == student.id, ExamSession.status == "published").all()
    result = []
    for s in sessions:
        paper = db.query(Paper).filter(Paper.id == s.paper_id).first()
        result.append(ResultListItem(session_id=s.id, paper_title=paper.title if paper else "Unknown",
                      total_score=s.total_score, status=s.status))
    return result


@router.get("/results/{session_id}")
def get_result_detail(session_id: int, db: Session = Depends(get_db), student: User = Depends(require_student)):
    session = db.query(ExamSession).filter(ExamSession.id == session_id, ExamSession.student_id == student.id,
                                            ExamSession.status == "published").first()
    if not session:
        raise HTTPException(status_code=404, detail="Result not found")
    answers = db.query(Answer).filter(Answer.session_id == session_id).all()
    answer_details = []
    for a in answers:
        q = db.query(Question).filter(Question.id == a.question_id).first()
        pts = a.paper_question.custom_points if a.paper_question else q.points
        answer_details.append({"id": a.id, "question_id": q.id, "question_text": q.question_text,
            "question_type": q.type, "student_answer": a.student_answer, "correct_answer": q.answer_text,
            "is_correct": a.is_correct, "score": a.score, "points": pts, "teacher_comment": a.teacher_comment})
    return {"session": ExamSessionResponse.model_validate(session), "answers": answer_details}
```

- [ ] **Step 2: Update main.py** — add `from routers import grading as grading_router` and `app.include_router(grading_router.router)`

---

### Task 13: Backend final main.py and seed script

**Files:**
- Update: `backend/main.py` (replace with final version)
- Create: `backend/seed.py`

- [ ] **Step 1: Replace main.py with final version**

```python
# backend/main.py (FINAL)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from database import init_db
from routers import auth as auth_router
from routers import questions as questions_router
from routers import papers as papers_router
from routers import exams as exams_router
from routers import grading as grading_router

app = FastAPI(title="Exam System")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router.router)
app.include_router(questions_router.router)
app.include_router(papers_router.router)
app.include_router(exams_router.router)
app.include_router(grading_router.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"error": "Frontend not built"}
```

- [ ] **Step 2: Create seed.py**

```python
# backend/seed.py
from database import init_db, SessionLocal
from models import User
from auth import hash_password

init_db()
db = SessionLocal()
for username, password, role in [("teacher1", "pass123", "teacher"), ("student1", "pass456", "student")]:
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"User {username} already exists")
        continue
    user = User(username=username, password_hash=hash_password(password), role=role)
    db.add(user)
    print(f"Created {role}: {username}")
db.commit()
db.close()
print("Seed done")
```

- [ ] **Step 3: Run seed**

```bash
cd backend && python seed.py
```

---

### Task 14: Frontend scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "exam-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.4.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "vite": "^6.0.0"
  }
}
```

- [ ] **Step 2: Create vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: { proxy: { '/api': 'http://localhost:8000' } },
  build: { outDir: 'dist' },
})
```

- [ ] **Step 3: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>考试系统</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 4: Install dependencies**

```bash
cd frontend && npm install
```

---

### Task 15: Frontend core (auth, api, router, main)

**Files:**
- Create: `frontend/src/main.js`
- Create: `frontend/src/auth.js`
- Create: `frontend/src/api.js`
- Create: `frontend/src/router.js`

- [ ] **Step 1: Create auth.js**

```javascript
// frontend/src/auth.js
const TOKEN_KEY = 'exam_token'
const ROLE_KEY = 'exam_role'
const USER_KEY = 'exam_username'

export function setAuth(token, role, username) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(ROLE_KEY, role)
  localStorage.setItem(USER_KEY, username)
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ROLE_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getToken() { return localStorage.getItem(TOKEN_KEY) }
export function getRole() { return localStorage.getItem(ROLE_KEY) }
export function getUsername() { return localStorage.getItem(USER_KEY) }
export function isLoggedIn() { return !!getToken() }
export function isTeacher() { return getRole() === 'teacher' }
export function isStudent() { return getRole() === 'student' }
```

- [ ] **Step 2: Create api.js**

```javascript
// frontend/src/api.js
import axios from 'axios'
import { getToken, clearAuth } from './auth'

const api = axios.create({ baseURL: '/api', timeout: 10000 })

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) { clearAuth(); window.location.href = '/login' }
    return Promise.reject(error)
  }
)

export default api
```

- [ ] **Step 3: Create router.js**

```javascript
// frontend/src/router.js
import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, isTeacher, isStudent } from './auth'

const routes = [
  { path: '/login', component: () => import('./views/Login.vue') },
  {
    path: '/teacher', component: () => import('./components/NavBar.vue'),
    meta: { requiresAuth: true, role: 'teacher' },
    children: [
      { path: '', redirect: '/teacher/questions' },
      { path: 'questions', component: () => import('./views/teacher/QuestionBank.vue') },
      { path: 'papers', component: () => import('./views/teacher/PaperBuilder.vue') },
      { path: 'exams', component: () => import('./views/teacher/ExamManager.vue') },
      { path: 'submissions', component: () => import('./views/teacher/Submissions.vue') },
      { path: 'grades', component: () => import('./views/teacher/Grades.vue') },
    ],
  },
  {
    path: '/student', component: () => import('./components/NavBar.vue'),
    meta: { requiresAuth: true, role: 'student' },
    children: [
      { path: '', redirect: '/student/exams' },
      { path: 'exams', component: () => import('./views/student/ExamList.vue') },
      { path: 'exam/:id', component: () => import('./views/student/ExamView.vue') },
      { path: 'results', component: () => import('./views/student/Results.vue') },
    ],
  },
  { path: '/', redirect: '/login' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isLoggedIn()) return '/login'
  if (to.meta.role === 'teacher' && !isTeacher()) return '/login'
  if (to.meta.role === 'student' && !isStudent()) return '/login'
})

export default router
```

- [ ] **Step 4: Create main.js**

```javascript
// frontend/src/main.js
import { createApp } from 'vue'
import router from './router'

const app = createApp({ template: '<router-view />' })
app.use(router)
app.mount('#app')
```

---

### Task 16: Login page

**Files:**
- Create: `frontend/src/views/Login.vue`

- [ ] **Step 1: Create Login.vue**

```vue
<template>
  <div class="login-container">
    <div class="login-card">
      <h1>考试系统</h1>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="username" type="text" placeholder="请输入用户名" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="请输入密码" required />
        </div>
        <button type="submit" :disabled="loading">{{ loading ? '登录中...' : '登录' }}</button>
        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { setAuth } from '../auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.post('/login', { username: username.value, password: password.value })
    setAuth(data.token, data.role, data.username)
    router.push(data.role === 'teacher' ? '/teacher' : '/student')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container { display:flex; justify-content:center; align-items:center; min-height:100vh; background:#f5f5f5; }
.login-card { background:white; padding:2rem; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1); width:360px; }
.login-card h1 { text-align:center; margin-bottom:1.5rem; }
.form-group { margin-bottom:1rem; }
.form-group label { display:block; margin-bottom:0.25rem; font-weight:500; }
.form-group input { width:100%; padding:0.5rem; border:1px solid #ddd; border-radius:4px; box-sizing:border-box; }
button { width:100%; padding:0.5rem; background:#3b82f6; color:white; border:none; border-radius:4px; cursor:pointer; font-size:1rem; }
button:disabled { opacity:0.6; cursor:not-allowed; }
.error { color:red; font-size:0.875rem; margin-top:0.5rem; }
</style>
```

---

### Task 17: NavBar component

**Files:**
- Create: `frontend/src/components/NavBar.vue`

- [ ] **Step 1: Create NavBar.vue**

```vue
<template>
  <div>
    <nav class="navbar">
      <span class="brand">考试系统</span>
      <div class="nav-links" v-if="isTeacher">
        <router-link to="/teacher/questions">题库</router-link>
        <router-link to="/teacher/papers">试卷</router-link>
        <router-link to="/teacher/exams">发布</router-link>
        <router-link to="/teacher/submissions">答卷</router-link>
        <router-link to="/teacher/grades">成绩</router-link>
      </div>
      <div class="nav-links" v-else-if="isStudent">
        <router-link to="/student/exams">考试</router-link>
        <router-link to="/student/results">成绩</router-link>
      </div>
      <div class="nav-right">
        <span class="user">{{ username }}</span>
        <button @click="handleLogout">退出</button>
      </div>
    </nav>
    <div class="content"><router-view /></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { getUsername, isTeacher, isStudent, clearAuth } from '../auth'

const router = useRouter()
const username = computed(getUsername)
function handleLogout() { clearAuth(); router.push('/login') }
</script>

<style scoped>
.navbar { display:flex; align-items:center; gap:1rem; padding:0.75rem 1.5rem; background:#1e293b; color:white; }
.brand { font-weight:bold; margin-right:1rem; }
.nav-links { display:flex; gap:0.75rem; }
.nav-links a { color:#cbd5e1; text-decoration:none; padding:0.25rem 0.5rem; border-radius:4px; }
.nav-links a.router-link-active { color:white; background:#334155; }
.nav-right { margin-left:auto; display:flex; align-items:center; gap:0.75rem; }
.nav-right button { padding:0.25rem 0.75rem; background:transparent; color:#cbd5e1; border:1px solid #475569; border-radius:4px; cursor:pointer; }
.content { padding:1.5rem; }
</style>
```

---

### Task 18: QuestionRenderer + Timer components

**Files:**
- Create: `frontend/src/components/QuestionRenderer.vue`
- Create: `frontend/src/components/Timer.vue`

- [ ] **Step 1: Create QuestionRenderer.vue**

```vue
<template>
  <div class="question-renderer">
    <h3>{{ label }}. {{ question.question_text }}</h3>
    <div v-if="question.type === 'choice_single'" class="options">
      <label v-for="(opt, idx) in question.options" :key="idx" class="option">
        <input type="radio" :name="'q_'+question.question_id" :value="optionLetter(idx)"
          :checked="modelValue === optionLetter(idx)" @change="$emit('update:modelValue', optionLetter(idx))" />
        {{ optionLetter(idx) }}. {{ opt }}
      </label>
    </div>
    <div v-else-if="question.type === 'choice_multi'" class="options">
      <label v-for="(opt, idx) in question.options" :key="idx" class="option">
        <input type="checkbox" :value="optionLetter(idx)" :checked="selectedLetters.includes(optionLetter(idx))"
          @change="toggleOption(optionLetter(idx))" />
        {{ optionLetter(idx) }}. {{ opt }}
      </label>
    </div>
    <div v-else-if="question.type === 'fill_blank'" class="fill">
      <input type="text" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" placeholder="请输入答案" />
    </div>
    <div v-else-if="question.type === 'essay'" class="essay">
      <textarea :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" rows="6" placeholder="请输入答案"></textarea>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ question: { type: Object, required: true }, modelValue: { type: String, default: '' }, label: { type: Number, default: 1 } })
const emit = defineEmits(['update:modelValue'])

function optionLetter(idx) { return String.fromCharCode(65 + idx) }
const selectedLetters = computed(() => props.modelValue ? props.modelValue.split(',') : [])

function toggleOption(letter) {
  const current = props.modelValue ? props.modelValue.split(',') : []
  const idx = current.indexOf(letter)
  if (idx >= 0) current.splice(idx, 1); else current.push(letter)
  emit('update:modelValue', current.sort().join(','))
}
</script>

<style scoped>
.question-renderer { padding:1rem 0; }
.question-renderer h3 { margin-bottom:1rem; }
.options { display:flex; flex-direction:column; gap:0.75rem; }
.option { display:flex; align-items:center; gap:0.5rem; padding:0.75rem; background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; cursor:pointer; }
.option:hover { background:#eff6ff; }
.fill input, .essay textarea { width:100%; padding:0.5rem; border:1px solid #ddd; border-radius:4px; font-size:1rem; box-sizing:border-box; }
</style>
```

- [ ] **Step 2: Create Timer.vue**

```vue
<template>
  <div class="timer" :class="{ warning: isWarning, danger: isDanger }">{{ display }}</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
const props = defineProps({ durationMinutes: { type: Number, required: true } })
const emit = defineEmits(['expired'])
const remainingSeconds = ref(props.durationMinutes * 60)
let interval = null
const display = computed(() => {
  const m = Math.floor(remainingSeconds.value / 60)
  const s = remainingSeconds.value % 60
  return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
})
const isWarning = computed(() => remainingSeconds.value < props.durationMinutes * 60 * 0.25)
const isDanger = computed(() => remainingSeconds.value < 60)
function tick() { remainingSeconds.value--; if (remainingSeconds.value <= 0) { clearInterval(interval); emit('expired') } }
onMounted(() => { interval = setInterval(tick, 1000) })
onUnmounted(() => { if (interval) clearInterval(interval) })
</script>

<style scoped>
.timer { font-size:1.2rem; font-weight:bold; font-family:monospace; }
.warning { color:#f59e0b; }
.danger { color:#ef4444; animation:blink 1s infinite; }
@keyframes blink { 50% { opacity:0.5; } }
</style>
```

---

### Task 19: Teacher - QuestionBank page

**Files:**
- Create: `frontend/src/views/teacher/QuestionBank.vue`

- [ ] **Step 1: Create QuestionBank.vue**

```vue
<template>
  <div>
    <div class="header"><h2>题库管理</h2>
      <div class="actions"><button @click="showImport=true">导入文本</button><button @click="showAdd=true">新增题目</button></div>
    </div>
    <div v-if="showImport" class="modal"><div class="modal-content">
      <h3>导入题目</h3>
      <textarea v-model="importText" rows="15" placeholder="粘贴题目文本..."></textarea>
      <div class="modal-actions"><button @click="doImport" :disabled="importing">{{ importing?'导入中...':'导入' }}</button><button @click="showImport=false">取消</button></div>
      <p v-if="importResult">{{ importResult.imported }} 题导入成功</p>
      <ul v-if="importResult?.errors?.length"><li v-for="e in importResult.errors" :key="e">{{ e }}</li></ul>
    </div></div>
    <div v-if="showAdd" class="modal"><div class="modal-content">
      <h3>新增题目</h3>
      <select v-model="nq.type"><option value="choice_single">单选题</option><option value="choice_multi">多选题</option><option value="fill_blank">填空题</option><option value="essay">简答题</option></select>
      <input v-model="nq.question_text" placeholder="题目内容" />
      <textarea v-if="nq.type.startsWith('choice')" v-model="nq.options_raw" placeholder="每行一个选项" rows="4"></textarea>
      <input v-model="nq.answer_text" placeholder="答案" />
      <input v-model.number="nq.points" type="number" placeholder="分值" />
      <div class="modal-actions"><button @click="doAdd" :disabled="adding">{{ adding?'保存中...':'保存' }}</button><button @click="showAdd=false">取消</button></div>
    </div></div>
    <table v-if="questions.length">
      <thead><tr><th>ID</th><th>类型</th><th>题目</th><th>答案</th><th>分值</th><th>操作</th></tr></thead>
      <tbody><tr v-for="q in questions" :key="q.id"><td>{{ q.id }}</td><td>{{ typeLabel(q.type) }}</td><td>{{ trunc(q.question_text,50) }}</td><td>{{ trunc(q.answer_text,30) }}</td><td>{{ q.points }}</td><td><button class="danger" @click="doDelete(q.id)">删除</button></td></tr></tbody>
    </table>
    <p v-else>暂无题目</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const questions = ref([])
const showImport = ref(false), showAdd = ref(false)
const importText = ref(''), importResult = ref(null), importing = ref(false), adding = ref(false)
const nq = ref({ type:'choice_single', question_text:'', options_raw:'', answer_text:'', points:5 })
const typeLabels = { choice_single:'单选', choice_multi:'多选', fill_blank:'填空', essay:'简答' }
function typeLabel(t) { return typeLabels[t]||t }
function trunc(s,n) { return s&&s.length>n ? s.slice(0,n)+'...' : s }
async function loadQuestions() { const { data } = await api.get('/questions/'); questions.value = data }
async function doImport() { importing.value=true; try { const { data } = await api.post('/questions/import',{file_text:importText.value}); importResult.value=data; await loadQuestions() } finally { importing.value=false } }
function parseOpts(raw) { return raw.split('\n').map(l=>l.replace(/^[A-Z][\.\)]\s*/,'').trim()).filter(Boolean) }
async function doAdd() { adding.value=true; try { const body={type:nq.value.type, question_text:nq.value.question_text, answer_text:nq.value.answer_text, points:nq.value.points}; if(nq.value.type.startsWith('choice')) body.options=parseOpts(nq.value.options_raw); await api.post('/questions/',body); showAdd.value=false; nq.value={type:'choice_single',question_text:'',options_raw:'',answer_text:'',points:5}; await loadQuestions() } finally { adding.value=false } }
async function doDelete(id) { if(confirm('确认删除？')){ await api.delete(`/questions/${id}`); await loadQuestions() } }
onMounted(loadQuestions)
</script>

<style scoped>
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; }
.actions { display:flex; gap:0.5rem; }
table { width:100%; border-collapse:collapse; }
th,td { padding:0.5rem; text-align:left; border-bottom:1px solid #e2e8f0; }
.modal { position:fixed; top:0;left:0;right:0;bottom:0; background:rgba(0,0,0,0.5); display:flex; justify-content:center; align-items:center; z-index:100; }
.modal-content { background:white; padding:1.5rem; border-radius:8px; width:600px; max-height:80vh; overflow-y:auto; }
.modal-content input,.modal-content textarea,.modal-content select { width:100%; padding:0.5rem; margin-bottom:0.5rem; border:1px solid #ddd; border-radius:4px; box-sizing:border-box; }
.modal-actions { display:flex; gap:0.5rem; }
.danger { background:#ef4444; color:white; }
</style>
```

---

### Task 20: Teacher - PaperBuilder page

**Files:**
- Create: `frontend/src/views/teacher/PaperBuilder.vue`

- [ ] **Step 1: Create PaperBuilder.vue**

```vue
<template>
  <div>
    <h2>试卷管理</h2>
    <button @click="showCreate=true">新建试卷</button>
    <div v-if="showCreate" class="modal"><div class="modal-content">
      <h3>新建试卷</h3>
      <input v-model="newTitle" placeholder="试卷名称" />
      <textarea v-model="newDesc" placeholder="描述（可选）" rows="3"></textarea>
      <div class="modal-actions"><button @click="doCreate">创建</button><button @click="showCreate=false">取消</button></div>
    </div></div>
    <table><thead><tr><th>ID</th><th>名称</th><th>状态</th><th>操作</th></tr></thead>
      <tbody><tr v-for="p in papers" :key="p.id"><td>{{ p.id }}</td><td>{{ p.title }}</td><td>{{ p.status }}</td>
        <td><button @click="openPaper(p)" v-if="p.status==='draft'">编辑</button><span v-else>-</span></td></tr></tbody>
    </table>
    <div v-if="editingPaper" class="editor">
      <h3>编辑: {{ editingPaper.title }}</h3>
      <p>已选 {{ paperQuestions.length }} 道题</p>
      <div v-for="(pq,i) in paperQuestions" :key="pq.id" class="pq-item">{{ i+1 }}. {{ pq.question?.question_text || '题目'+pq.question_id }}</div>
      <h4>添加题目</h4>
      <input v-model="searchQ" placeholder="搜索题目..." />
      <div v-for="q in filtered" :key="q.id" class="q-item"><span>{{ q.id }}. {{ trunc(q.question_text,60) }}</span><button @click="addQ(q.id)">添加</button></div>
      <h4>随机选题</h4>
      <input v-model.number="randCount" type="number" placeholder="数量" style="width:80px" />
      <button @click="doRandom">随机选择</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'
const papers = ref([]), showCreate = ref(false), newTitle = ref(''), newDesc = ref('')
const editingPaper = ref(null), paperQuestions = ref([]), allQ = ref([]), searchQ = ref(''), randCount = ref(5)
const filtered = computed(() => { if(!searchQ.value) return allQ.value; const s=searchQ.value.toLowerCase(); return allQ.value.filter(q=>q.id.toString().includes(s)||q.question_text.toLowerCase().includes(s)) })
function trunc(s,n){ return s&&s.length>n?s.slice(0,n)+'...':s }
async function loadPapers(){ const { data }=await api.get('/papers/'); papers.value=data }
async function loadAllQ(){ const { data }=await api.get('/questions/'); allQ.value=data }
async function doCreate(){ await api.post('/papers/',{title:newTitle.value,description:newDesc.value}); showCreate.value=false; newTitle.value=''; newDesc.value=''; await loadPapers() }
async function openPaper(p){ editingPaper.value=p; const { data }=await api.get(`/papers/${p.id}/questions`); paperQuestions.value=data }
async function addQ(id){ await api.post(`/papers/${editingPaper.value.id}/build`,{question_ids:[id]}); const { data }=await api.get(`/papers/${editingPaper.value.id}/questions`); paperQuestions.value=data }
async function doRandom(){ await api.post(`/papers/${editingPaper.value.id}/build`,{strategy:'random',count:randCount.value}); const { data }=await api.get(`/papers/${editingPaper.value.id}/questions`); paperQuestions.value=data }
onMounted(()=>{ loadPapers(); loadAllQ() })
</script>

<style scoped>
table{width:100%;border-collapse:collapse;} th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
.modal{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;justify-content:center;align-items:center;z-index:100;}
.modal-content{background:white;padding:1.5rem;border-radius:8px;width:400px;} .modal-content input,.modal-content textarea{width:100%;padding:0.5rem;margin-bottom:0.5rem;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;}
.modal-actions{display:flex;gap:0.5rem;}
.editor{margin-top:1.5rem;padding:1rem;background:#f8fafc;border-radius:8px;}
.q-item{display:flex;justify-content:space-between;padding:0.25rem 0;}
</style>
```

---

### Task 21: Teacher - ExamManager page

**Files:**
- Create: `frontend/src/views/teacher/ExamManager.vue`

- [ ] **Step 1: Create ExamManager.vue**

```vue
<template>
  <div>
    <h2>发布管理</h2>
    <table><thead><tr><th>ID</th><th>试卷</th><th>状态</th><th>时间窗口</th><th>时长</th><th>操作</th></tr></thead>
      <tbody><tr v-for="p in papers" :key="p.id"><td>{{ p.id }}</td><td>{{ p.title }}</td><td>{{ p.status }}</td>
        <td>{{ fmt(p.window_start) }} ~ {{ fmt(p.window_end) }}</td><td>{{ p.duration_minutes?p.duration_minutes+' 分钟':'-' }}</td>
        <td><button v-if="p.status==='draft'" @click="showPub(p)">发布</button>
            <button v-if="p.status==='active'" class="danger" @click="doUnpub(p)">下线</button></td></tr></tbody>
    </table>
    <div v-if="pubPaper" class="modal"><div class="modal-content">
      <h3>发布: {{ pubPaper.title }}</h3>
      <label>开始时间</label><input v-model="wStart" type="datetime-local" />
      <label>结束时间</label><input v-model="wEnd" type="datetime-local" />
      <label>考试时长（分钟）</label><input v-model.number="dur" type="number" />
      <div class="modal-actions"><button @click="doPub">确认发布</button><button @click="pubPaper=null">取消</button></div>
    </div></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const papers = ref([]), pubPaper = ref(null), wStart = ref(''), wEnd = ref(''), dur = ref(60)
function fmt(d){ return d?new Date(d).toLocaleString():'-' }
async function load(){ const { data }=await api.get('/papers/'); papers.value=data }
function showPub(p){ pubPaper.value=p; const now=new Date(); const later=new Date(now.getTime()+3600000); wStart.value=now.toISOString().slice(0,16); wEnd.value=later.toISOString().slice(0,16); dur.value=60 }
async function doPub(){ await api.post(`/papers/${pubPaper.value.id}/publish`,{window_start:wStart.value,window_end:wEnd.value,duration_minutes:dur.value}); pubPaper.value=null; await load() }
async function doUnpub(p){ await api.put(`/papers/${p.id}/unpublish`); await load() }
onMounted(load)
</script>

<style scoped>
table{width:100%;border-collapse:collapse;} th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
.modal{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;justify-content:center;align-items:center;z-index:100;}
.modal-content{background:white;padding:1.5rem;border-radius:8px;width:400px;} .modal-content input,.modal-content label{width:100%;display:block;margin-bottom:0.5rem;} .modal-content input{padding:0.5rem;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;}
.modal-actions{display:flex;gap:0.5rem;} .danger{background:#ef4444;color:white;}
</style>
```

---

### Task 22: Teacher - Submissions + Grades pages

**Files:**
- Create: `frontend/src/views/teacher/Submissions.vue`
- Create: `frontend/src/views/teacher/Grades.vue`

- [ ] **Step 1: Create Submissions.vue**

```vue
<template>
  <div>
    <h2>答卷查看</h2>
    <table><thead><tr><th>学生</th><th>状态</th><th>自动分</th><th>手动分</th><th>总分</th><th>提交时间</th><th>操作</th></tr></thead>
      <tbody><tr v-for="s in subs" :key="s.session_id"><td>{{ s.student_username }}</td><td>{{ s.status }}</td>
        <td>{{ s.auto_score??'-' }}</td><td>{{ s.manual_score??'-' }}</td><td>{{ s.total_score??'-' }}</td>
        <td>{{ s.submit_time?new Date(s.submit_time).toLocaleString():'-' }}</td>
        <td><button @click="viewDetail(s.session_id)">查看</button><button @click="doPub(s.session_id)" v-if="s.status!=='published'">发布</button></td></tr></tbody>
    </table>
    <div v-if="detail" class="detail">
      <h3>答卷详情</h3>
      <div v-for="a in detail.answers" :key="a.id" class="card">
        <h4>{{ a.question_text }} ({{ a.question_type }})</h4>
        <p>学生答案: {{ a.student_answer }}</p>
        <p>正确答案: {{ a.correct_answer }}</p>
        <p>结果: {{ a.is_correct===null?'待评':(a.is_correct?'正确':'错误') }}</p>
        <p>得分: {{ a.score??'未评分' }} / {{ a.points }}</p>
        <div v-if="a.question_type==='essay'" class="eg">
          <input v-model="a._score" placeholder="评分" type="number" />
          <input v-model="a._comment" placeholder="评语" />
          <button @click="doScore(a)">提交评分</button>
        </div>
      </div>
      <button @click="detail=null">关闭</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const subs = ref([]), detail = ref(null)
async function load(){ const { data }=await api.get('/submissions'); subs.value=data }
async function viewDetail(sid){ const { data }=await api.get(`/submissions/${sid}/detail`); detail.value=data; detail.value.answers.forEach(a=>{ a._score=a.score||''; a._comment=a.teacher_comment||'' }) }
async function doScore(a){ await api.post(`/answers/${a.id}/score`,{score:parseFloat(a._score),comment:a._comment}); await viewDetail(detail.value.session.id); await load() }
async function doPub(sid){ await api.post(`/submissions/${sid}/publish`); await load() }
onMounted(load)
</script>

<style scoped>
table{width:100%;border-collapse:collapse;} th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
.detail{margin-top:1rem;padding:1rem;background:#f8fafc;border-radius:8px;}
.card{padding:1rem;background:white;margin-bottom:0.5rem;border-radius:4px;}
.eg{display:flex;gap:0.5rem;margin-top:0.5rem;} .eg input{padding:0.25rem;border:1px solid #ddd;border-radius:4px;}
</style>
```

- [ ] **Step 2: Create Grades.vue**

```vue
<template>
  <div>
    <h2>成绩列表</h2>
    <table><thead><tr><th>学生</th><th>自动分</th><th>手动分</th><th>总分</th><th>状态</th><th>提交时间</th></tr></thead>
      <tbody><tr v-for="s in subs" :key="s.session_id"><td>{{ s.student_username }}</td><td>{{ s.auto_score??'-' }}</td><td>{{ s.manual_score??'-' }}</td>
        <td><strong>{{ s.total_score??'-' }}</strong></td><td>{{ s.status }}</td><td>{{ s.submit_time?new Date(s.submit_time).toLocaleString():'-' }}</td></tr></tbody>
    </table>
    <p v-if="!subs.length">暂无答卷</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const subs = ref([])
async function load(){ const { data }=await api.get('/submissions'); subs.value=data }
onMounted(load)
</script>

<style scoped>
table{width:100%;border-collapse:collapse;} th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
</style>
```

---

### Task 23: Student - ExamList page

**Files:**
- Create: `frontend/src/views/student/ExamList.vue`

- [ ] **Step 1: Create ExamList.vue**

```vue
<template>
  <div>
    <h2>当前考试</h2>
    <div v-if="exams.length" class="grid">
      <div v-for="exam in exams" :key="exam.id" class="card">
        <h3>{{ exam.title }}</h3>
        <p>{{ exam.description }}</p>
        <p>题目: {{ exam.question_count }} | 时长: {{ exam.duration_minutes }} 分钟</p>
        <p>开放至: {{ new Date(exam.window_end).toLocaleString() }}</p>
        <button @click="start(exam.id)">开始考试</button>
      </div>
    </div>
    <p v-else>暂无可用考试</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'
const router = useRouter()
const exams = ref([])
async function load(){ const { data }=await api.get('/exams/available'); exams.value=data }
async function start(pid){ const { data }=await api.post('/exams/start',{paper_id:pid}); router.push(`/student/exam/${data.id}`) }
onMounted(load)
</script>

<style scoped>
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem;}
.card{padding:1rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;}
.card h3{margin-bottom:0.5rem;} .card p{margin:0.25rem 0;color:#64748b;}
.card button{margin-top:0.75rem;padding:0.5rem 1rem;background:#3b82f6;color:white;border:none;border-radius:4px;cursor:pointer;}
</style>
```

---

### Task 24: Student - ExamView page

**Files:**
- Create: `frontend/src/views/student/ExamView.vue`

- [ ] **Step 1: Create ExamView.vue**

```vue
<template>
  <div class="exam" v-if="questions.length">
    <div class="header">
      <Timer :duration-minutes="duration" @expired="handleSubmit" />
      <span>题目 {{ ci+1 }}/{{ questions.length }}</span>
      <button @click="next" :disabled="ci>=questions.length-1">下一题</button>
    </div>
    <div class="body">
      <QuestionRenderer :question="questions[ci]" v-model="answers[ci]" :label="ci+1" />
    </div>
    <div class="footer">
      <button @click="prev" :disabled="ci===0">上一题</button>
      <button @click="toggleMark" :class="{marked:marked.has(ci)}">标记</button>
      <div class="dots">
        <button v-for="(q,i) in questions" :key="q.question_id" @click="ci=i" :class="{active:i===ci,answered:answers[i]}">{{ i+1 }}</button>
      </div>
      <button class="submit" @click="handleSubmit">提交试卷</button>
    </div>
  </div>
  <div v-else class="loading">加载中...</div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'
import QuestionRenderer from '../../components/QuestionRenderer.vue'
import Timer from '../../components/Timer.vue'

const route = useRoute(), router = useRouter()
const sessionId = parseInt(route.params.id)
const questions = ref([]), answers = ref({}), ci = ref(0), marked = ref(new Set()), duration = ref(60)
let saveInterval = null

async function load(){
  const { data } = await api.get(`/exams/${sessionId}/questions`)
  questions.value = data
  const saved = localStorage.getItem('ea_'+sessionId)
  if (saved) answers.value = JSON.parse(saved)
}

watch(answers, (v) => localStorage.setItem('ea_'+sessionId, JSON.stringify(v)), { deep: true })

async function saveCurrent(){
  const q = questions.value[ci.value]
  if (!q || !answers.value[ci.value]) return
  try { await api.put(`/exams/${sessionId}/answer`, { question_id: q.question_id, answer: answers.value[ci.value] }) } catch(e) {}
}

onMounted(()=>{ load(); saveInterval=setInterval(saveCurrent, 10000) })
onUnmounted(()=>{ if(saveInterval) clearInterval(saveInterval) })

function prev(){ if(ci.value>0) ci.value-- }
function next(){ if(ci.value<questions.value.length-1) ci.value++ }
function toggleMark(){ if(marked.value.has(ci.value)) marked.value.delete(ci.value); else marked.value.add(ci.value); marked.value=new Set(marked.value) }

async function handleSubmit(){
  if(!confirm('确认提交？')) return
  for(const idx in answers.value){
    if(answers.value[idx]){ const q=questions.value[parseInt(idx)]; if(q) await api.put(`/exams/${sessionId}/answer`,{question_id:q.question_id,answer:answers.value[idx]}) }
  }
  await api.post(`/exams/${sessionId}/submit`)
  localStorage.removeItem('ea_'+sessionId)
  router.push('/student/results')
}
</script>

<style scoped>
.exam{min-height:100vh;display:flex;flex-direction:column;}
.header{display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;background:#1e293b;color:white;}
.body{padding:1.5rem;flex:1;}
.footer{display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;background:#f8fafc;border-top:1px solid #e2e8f0;}
.dots{display:flex;gap:0.25rem;flex-wrap:wrap;}
.dots button{width:28px;height:28px;border:1px solid #e2e8f0;background:white;border-radius:4px;cursor:pointer;font-size:0.75rem;}
.dots button.active{background:#3b82f6;color:white;}
.dots button.answered{border-color:#10b981;}
.marked{background:#f59e0b;color:white!important;}
.submit{background:#ef4444;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer;}
.loading{text-align:center;padding:2rem;}
</style>
```

---

### Task 25: Student - Results page

**Files:**
- Create: `frontend/src/views/student/Results.vue`

- [ ] **Step 1: Create Results.vue**

```vue
<template>
  <div>
    <h2>我的成绩</h2>
    <div v-if="detail" class="detail">
      <h3>考试成绩</h3>
      <p>总分: <strong>{{ detail.session?.total_score }}</strong></p>
      <div v-for="a in detail.answers" :key="a.id" class="card">
        <h4>{{ a.question_text }}</h4>
        <p>你的答案: {{ a.student_answer }}</p>
        <p>正确答案: {{ a.correct_answer }}</p>
        <p>结果: {{ a.is_correct===null?'已评分':(a.is_correct?'正确':'错误') }}</p>
        <p>得分: {{ a.score }} / {{ a.points }}</p>
        <p v-if="a.teacher_comment">评语: {{ a.teacher_comment }}</p>
      </div>
      <button @click="detail=null">返回</button>
    </div>
    <table v-else><thead><tr><th>试卷</th><th>总分</th><th>状态</th><th>操作</th></tr></thead>
      <tbody><tr v-for="r in results" :key="r.session_id"><td>{{ r.paper_title }}</td><td>{{ r.total_score??'评分中' }}</td>
        <td>{{ r.status }}</td><td><button @click="view(r.session_id)">查看</button></td></tr></tbody>
    </table>
    <p v-if="!results.length">暂无成绩</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
const results = ref([]), detail = ref(null)
async function load(){ const { data }=await api.get('/results'); results.value=data }
async function view(sid){ const { data }=await api.get(`/results/${sid}`); detail.value=data }
onMounted(load)
</script>

<style scoped>
table{width:100%;border-collapse:collapse;} th,td{padding:0.5rem;text-align:left;border-bottom:1px solid #e2e8f0;}
.detail{padding:1rem;} .card{padding:1rem;background:#f8fafc;margin-bottom:0.5rem;border-radius:4px;}
</style>
```

---

### Task 26: Build frontend + final integration

- [ ] **Step 1: Build frontend**

```bash
cd frontend && npm run build
```

- [ ] **Step 2: Start backend and verify SPA serving**

```bash
cd backend && uvicorn main:app --port 8000 &
curl http://localhost:8000/ | head -5
pkill -f "uvicorn main:app"
```

- [ ] **Step 3: End-to-end test**

1. Register teacher via seed: `cd backend && python seed.py`
2. Login as teacher, import questions, create/publish paper
3. Login as student, start exam, answer, submit
4. Teacher views submission, scores essays, publishes
5. Student views result

---

### Task 27: .gitignore + commit

- [ ] **Step 1: Create .gitignore**

```
__pycache__/
*.pyc
data/*.db
node_modules/
frontend/dist/
.superpowers/
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: implement exam system with teacher management and student exam-taking"
```




