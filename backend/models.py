# backend/models.py
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    papers = relationship("Paper", back_populates="creator", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="creator", cascade="all, delete-orphan")
    sessions = relationship("ExamSession", back_populates="student", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(Text, nullable=True)  # JSON string for choice options
    answer_text = Column(Text, nullable=False)
    points = Column(Integer, default=5)
    category = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    creator = relationship("User", back_populates="questions")
    paper_questions = relationship("PaperQuestion", back_populates="question")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class Paper(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    status = Column(String, nullable=False, default="draft")
    window_start = Column(DateTime, nullable=True)
    window_end = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    creator = relationship("User", back_populates="papers")
    paper_questions = relationship("PaperQuestion", back_populates="paper", cascade="all, delete-orphan")
    sessions = relationship("ExamSession", back_populates="paper", cascade="all, delete-orphan")


class PaperQuestion(Base):
    __tablename__ = "paper_questions"
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    order_index = Column(Integer, nullable=False)
    custom_points = Column(Integer, nullable=True)
    paper = relationship("Paper", back_populates="paper_questions")
    question = relationship("Question", back_populates="paper_questions")
    answers = relationship("Answer", back_populates="paper_question", cascade="all, delete-orphan")


class ExamSession(Base):
    __tablename__ = "exam_sessions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    start_time = Column(DateTime, server_default=func.now())
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
    student_answer = Column(Text, default="")
    is_correct = Column(Boolean, nullable=True)
    score = Column(Float, nullable=True)
    teacher_comment = Column(Text, nullable=True)
    session = relationship("ExamSession", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    paper_question = relationship("PaperQuestion", back_populates="answers")
