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
