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
            db.flush()
            created += 1
        except Exception as e:
            errors.append(f"Question {i+1}: {str(e)}")
            db.rollback()
    db.commit()
    return ImportResponse(imported=created, errors=errors)
