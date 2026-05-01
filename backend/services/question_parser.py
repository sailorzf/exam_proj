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
        qtype = "choice_multi" if "(多选)" in question_text or "（多选）" in question_text else "choice_single"
        question_text = re.sub(r'\s*（多选）\s*|\s*\(多选\)\s*', '', question_text).strip()
        return {"type": qtype, "question_text": question_text, "options": options, "answer_text": answer_text}
    elif "___" in question_text or "____" in question_text:
        return {"type": "fill_blank", "question_text": question_text, "options": None, "answer_text": answer_text}
    else:
        return {"type": "essay", "question_text": question_text, "options": None, "answer_text": answer_text}
