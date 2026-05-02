import json
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from database import get_db
from models import User, Question, Category
from schemas import QuestionCreate, QuestionUpdate, QuestionResponse, ImportWithCategoryRequest, ImportResponse
from auth import require_teacher
from services.question_parser import parse_questions

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.get("/")
def list_questions(page: int = 1, limit: int = 20, category: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Question)
    if category:
        q = q.filter(Question.category == category)
    total = q.count()
    items = q.order_by(Question.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [QuestionResponse.model_validate(i) for i in items], "total": total, "page": page, "limit": limit}


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(Category).all()
    result = []
    for c in cats:
        count = db.query(Question).filter(Question.category == c.name).count()
        result.append({"id": c.id, "name": c.name, "count": count, "created_at": c.created_at})
    return result


@router.post("/", response_model=QuestionResponse, status_code=201)
def create_question(req: QuestionCreate, db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    # Auto-register category if new
    if req.category:
        existing_cat = db.query(Category).filter(Category.name == req.category).first()
        if not existing_cat:
            db.add(Category(name=req.category))
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


class ImportWithCategoryRequest(BaseModel):
    file_text: str
    category: Optional[str] = None


class CategoryRequest(BaseModel):
    name: str


class CategoryCreate(BaseModel):
    name: str


@router.post("/import", response_model=ImportResponse)
def import_questions(req: ImportWithCategoryRequest, db: Session = Depends(get_db), teacher: User = Depends(require_teacher)):
    parsed = parse_questions(req.file_text)
    errors = []
    created = 0
    for i, item in enumerate(parsed):
        try:
            # Auto-register category if new
            if req.category:
                existing_cat = db.query(Category).filter(Category.name == req.category).first()
                if not existing_cat:
                    db.add(Category(name=req.category))
            q = Question(
                type=item["type"], question_text=item["question_text"],
                options=json.dumps(item["options"]) if item.get("options") else None,
                answer_text=item["answer_text"], points=5, category=req.category,
                created_by=teacher.id,
            )
            db.add(q)
            db.flush()
            created += 1
        except Exception as e:
            errors.append(f"Question {i+1}: {str(e)}")
            db.rollback()
    db.commit()
    return ImportResponse(imported=created, errors=errors)


@router.post("/category", status_code=201)
def create_category(req: CategoryCreate, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    existing = db.query(Category).filter(Category.name == req.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="该科目已存在")
    cat = Category(name=req.name)
    db.add(cat)
    db.commit()
    return {"name": req.name}


@router.put("/category/{old_name}")
def update_category(old_name: str, req: CategoryRequest, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    cat = db.query(Category).filter(Category.name == old_name).first()
    if not cat:
        raise HTTPException(status_code=404, detail="科目不存在")
    # Check new name doesn't conflict
    conflict = db.query(Category).filter(Category.name == req.name, Category.id != cat.id).first()
    if conflict:
        raise HTTPException(status_code=400, detail="该科目已存在")
    # Rename category on all questions
    db.query(Question).filter(Question.category == old_name).update({Question.category: req.name})
    cat.name = req.name
    db.commit()


@router.delete("/category/{name}", status_code=204)
def delete_category(name: str, db: Session = Depends(get_db), _teacher: User = Depends(require_teacher)):
    cat = db.query(Category).filter(Category.name == name).first()
    if not cat:
        raise HTTPException(status_code=404, detail="科目不存在")
    # Delete all questions in this category
    db.query(Question).filter(Question.category == name).delete()
    db.delete(cat)
    db.commit()
