# backend/routers/papers.py
import json
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


@router.get("/{paper_id}/questions")
def get_paper_questions(paper_id: int, db: Session = Depends(get_db)):
    p = db.query(Paper).filter(Paper.id == paper_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    pqs = db.query(PaperQuestion).filter(PaperQuestion.paper_id == paper_id).order_by(PaperQuestion.order_index).all()
    result = []
    for pq in pqs:
        q = db.query(Question).filter(Question.id == pq.question_id).first()
        if q:
            result.append({
                "pq_id": pq.id, "paper_id": pq.paper_id, "question_id": pq.question_id,
                "order_index": pq.order_index, "custom_points": pq.custom_points,
                "type": q.type, "question_text": q.question_text,
                "options": json.loads(q.options) if q.options else None,
                "answer_text": q.answer_text, "points": q.points,
            })
    return result


@router.delete("/{paper_id}/questions/{pq_id}", status_code=204)
def delete_paper_question(paper_id: int, pq_id: int, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    pq = db.query(PaperQuestion).filter(PaperQuestion.id == pq_id, PaperQuestion.paper_id == paper_id).first()
    if not pq:
        raise HTTPException(status_code=404, detail="Paper question not found")
    db.delete(pq)
    db.commit()


@router.post("/{paper_id}/questions/clear", status_code=204)
def clear_paper_questions(paper_id: int, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    p = db.query(Paper).filter(Paper.id == paper_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    db.query(PaperQuestion).filter(PaperQuestion.paper_id == paper_id).delete()
    db.commit()


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
