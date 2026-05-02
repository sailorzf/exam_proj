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

        pts = (answer.paper_question.custom_points or question.points) if answer.paper_question else question.points

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
    session.manual_score = 0.0
    session.total_score = auto_score
    session.status = "submitted"
    db.flush()
    return {"auto_score": auto_score, "total_questions": len(answers), "graded_count": graded_count}
