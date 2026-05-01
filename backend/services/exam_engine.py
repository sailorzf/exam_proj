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
