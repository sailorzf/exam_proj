# backend/schemas.py
import json
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str
    is_admin: bool = False


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

    @field_validator("options", mode="before")
    @classmethod
    def parse_options(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return None
        return v


class ImportRequest(BaseModel):
    file_text: str


class ImportWithCategoryRequest(BaseModel):
    file_text: str
    category: Optional[str] = None


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


class WrongAnswerDetail(BaseModel):
    question_id: int
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    student_answer: str
    correct_answer: str
    score: Optional[float]
    points: int

    @field_validator("options", mode="before")
    @classmethod
    def parse_options(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return None
        return v


class SubmitExamResponse(BaseModel):
    session: ExamSessionResponse
    grading: dict
    wrong_answers: List[WrongAnswerDetail]


class AnswerDetail(BaseModel):
    id: int
    question_id: int
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    student_answer: str
    correct_answer: str
    is_correct: Optional[bool]
    score: Optional[float]
    points: int
    teacher_comment: Optional[str] = None

    @field_validator("options", mode="before")
    @classmethod
    def parse_options(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return None
        return v


class SubmissionDetail(BaseModel):
    session: ExamSessionResponse
    answers: List[AnswerDetail]


class SubmissionListItem(BaseModel):
    session_id: int
    paper_id: int
    student_username: str
    student_name: Optional[str] = None
    status: str
    auto_score: Optional[float]
    manual_score: Optional[float]
    total_score: Optional[float]
    submit_time: Optional[datetime]


class ResultListItem(BaseModel):
    session_id: int
    paper_title: str
    auto_score: Optional[float]
    manual_score: Optional[float]
    total_score: Optional[float]
    status: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    class_name: Optional[str] = None


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    class_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_admin: bool
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    class_name: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class UserImportResponse(BaseModel):
    imported: int
    errors: List[str] = []


class UserProfileUpdate(BaseModel):
    password: Optional[str] = None
    old_password: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    class_name: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: int
    username: str
    role: str
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    class_name: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True
