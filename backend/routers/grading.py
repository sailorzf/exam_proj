# backend/routers/grading.py
from sqlalchemy import func
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
        manual_score = manual if manual > 0 else (s.manual_score or 0)
        total_score = (s.auto_score or 0) + manual_score
        paper = db.query(Paper).filter(Paper.id == s.paper_id).first()
        result.append(SubmissionListItem(
            session_id=s.id, student_username=student.username if student else "Unknown",
            status=s.status, auto_score=s.auto_score, manual_score=manual_score,
            total_score=total_score, submit_time=s.submit_time))
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
        pts = (a.paper_question.custom_points or q.points) if a.paper_question else q.points
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
        essay_total = db.query(Answer).filter(Answer.session_id == session.id, Answer.score.isnot(None)).with_entities(func.sum(Answer.score)).scalar()
        session.manual_score = essay_total or 0
        session.total_score = (session.auto_score or 0) + (session.manual_score or 0)
        db.commit()
    return {"scored": True}


@router.post("/submissions/{session_id}/publish")
def publish_submission(session_id: int, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Submission not found")
    essay_total = db.query(Answer).filter(Answer.session_id == session_id, Answer.score.isnot(None)).with_entities(func.sum(Answer.score)).scalar()
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


@router.get("/results/{session_id}", response_model=SubmissionDetail)
def get_result_detail(session_id: int, db: Session = Depends(get_db), student: User = Depends(require_student)):
    session = db.query(ExamSession).filter(ExamSession.id == session_id, ExamSession.student_id == student.id,
                                            ExamSession.status == "published").first()
    if not session:
        raise HTTPException(status_code=404, detail="Result not found")
    answers = db.query(Answer).filter(Answer.session_id == session_id).all()
    answer_details = []
    for a in answers:
        q = db.query(Question).filter(Question.id == a.question_id).first()
        pts = (a.paper_question.custom_points or q.points) if a.paper_question else q.points
        answer_details.append(AnswerDetail(
            id=a.id, question_id=q.id, question_text=q.question_text, question_type=q.type,
            student_answer=a.student_answer, correct_answer=q.answer_text,
            is_correct=a.is_correct, score=a.score, points=pts, teacher_comment=a.teacher_comment))
    return SubmissionDetail(session=ExamSessionResponse.model_validate(session), answers=answer_details)
