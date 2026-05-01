# Exam System Design Document

**Date:** 2026-05-01
**Status:** Draft

## 1. Overview

A lightweight online exam system for small-scale public-facing exams (10-50 concurrent users). Teachers manage questions, create and publish exams, review submissions, and release grades. Students take exams with timed sessions and view their results afterward.

## 2. Constraints

| Constraint | Decision |
|---|---|
| Tech stack | React/Vue SPA + Python FastAPI + SQLite |
| User scale | Small (10-50 concurrent) |
| Deployment | Public network access |
| Anti-cheating | Minimum (no special measures) |
| Time control | Both time window (start/end date) AND per-exam duration |
| Grading | Auto-grade choice/fill questions; essays graded manually by teacher |

## 3. Architecture

Three-tier monolithic deployment on a single machine:

```
Browser ──REST/JSON──▶ FastAPI ──SQLAlchemy──▶ SQLite
                         │
                         └── serves static SPA build files
```

- Frontend SPA shares codebase, routes differ by role (teacher/student)
- FastAPI serves both API and static files
- SQLite database, no external services needed
- JWT-based authentication, role-checked per endpoint

## 4. Database Schema

### users
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| username | VARCHAR UNIQUE | |
| password_hash | VARCHAR | bcrypt |
| role | VARCHAR | 'teacher' or 'student' |
| created_at | DATETIME | |

### questions
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| type | VARCHAR | 'choice_single', 'choice_multi', 'fill_blank', 'essay' |
| question_text | TEXT | |
| options | JSON | null for fill_blank/essay |
| answer_text | TEXT | reference answer |
| points | INTEGER | default 5 |
| category | VARCHAR | nullable |
| created_by | INTEGER FK → users.id | |
| created_at | DATETIME | |

### papers
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| title | VARCHAR | |
| description | TEXT | nullable |
| created_by | INTEGER FK → users.id | |
| created_at | DATETIME | |
| updated_at | DATETIME | |
| status | VARCHAR | 'draft', 'active', 'offline' |
| window_start | DATETIME | nullable, exam open date |
| window_end | DATETIME | nullable, exam close date |
| duration_minutes | INTEGER | nullable, exam timer duration |

### paper_questions
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| paper_id | INTEGER FK → papers.id | |
| question_id | INTEGER FK → questions.id | |
| order_index | INTEGER | display order |
| custom_points | INTEGER | nullable, override default points |

### exam_sessions
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| student_id | INTEGER FK → users.id | |
| paper_id | INTEGER FK → papers.id | |
| start_time | DATETIME | |
| submit_time | DATETIME | nullable |
| status | VARCHAR | 'in_progress', 'submitted', 'pending_review', 'published' |
| auto_score | FLOAT | nullable, auto-graded score |
| manual_score | FLOAT | nullable, teacher-graded essay score |
| total_score | FLOAT | nullable, auto_score + manual_score |

### answers
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| session_id | INTEGER FK → exam_sessions.id | |
| question_id | INTEGER FK → questions.id | |
| student_answer | TEXT | |
| is_correct | BOOLEAN | nullable, null for essays |
| score | FLOAT | nullable |
| teacher_comment | TEXT | nullable |

## 5. Module Design

### 5.1 Auth Module
- `POST /login` — username + password → JWT token + role
- `POST /register` — teacher-only endpoint to create accounts
- JWT: HS256, 8-hour expiry, bearer token required on all API routes
- Middleware checks token validity and role authorization

### 5.2 QuestionBank Module
- `GET /questions` — list with optional tag/category filter
- `POST /questions` — create single question
- `PUT /questions/{id}` — update question
- `DELETE /questions/{id}` — delete question
- `POST /questions/import` — parse text file, batch create questions

**Text Parser Logic:**
1. Split input by lines starting with "Q" (question markers)
2. For each block, detect question type:
   - Lines starting with A/B/C/D followed by "." → choice question
   - Text contains "___" or "____" → fill-in-blank
   - Otherwise → essay
   - If question text contains "(多选)" → multi-choice, else single-choice
3. Extract answer from line starting with "A:" or "答案:"
4. Choice answers: single letter "A" or comma-separated "A,B,C"

### 5.3 PaperBuilder Module
- `GET /papers` — list all papers (teacher)
- `POST /papers` — create new paper (draft)
- `PUT /papers/{id}` — update paper metadata
- `DELETE /papers/{id}` — delete draft paper
- `POST /papers/{id}/build` — add questions to paper
  - Body: `{question_ids: [...]}` (specified selection)
  - Body: `{strategy: "random", count: N, tags: [...]}` (random selection)
- `PUT /papers/{id}/publish` — set status to active, configure window_start, window_end, duration_minutes
- `PUT /papers/{id}/unpublish` — set status to offline

### 5.4 ExamRunner Module (Student)
- `GET /exams/available` — list active exams within time window
- `POST /exams/start` — {paper_id} → creates exam_session, returns first question
- `GET /exams/{session_id}/question/{index}` — get question by index (no answer data)
- `GET /exams/{session_id}/questions` — get all question metadata (titles, types, order)
- `PUT /exams/{session_id}/answer` — {question_id, answer} — save answer
- `POST /exams/{session_id}/submit` — finalize submission, triggers auto-grading

**Timer behavior:**
- Client-side countdown from duration_minutes
- Answers saved to server on each answer change (or local storage fallback)
- Timer reaching 0 auto-triggers submit

### 5.5 GradingEngine Module
- `GET /submissions/{id}/detail` — teacher views submission with auto-graded results
- `POST /answers/{id}/score` — {score, comment} — teacher grades essay question
- `POST /submissions/{id}/publish` — set status to published, makes results visible to student

**Auto-grading logic:**
- Single choice: exact match with answer_text
- Multi choice: exact match of sorted answer set (e.g., "A,B" == "B,A")
- Fill blank: case-insensitive string match after stripping whitespace and common punctuation variants
- Essay: skipped (is_correct = null, score = null)

### 5.6 Dashboard Module
- `GET /papers/{id}/results` — teacher: list all submissions for a paper with scores
- `GET /results` — student: list published exam results
- `GET /results/{session_id}` — student: detailed result with per-question correctness, scores, and teacher comments

## 6. Frontend Structure

### Pages
| Route | Role | Component |
|---|---|---|
| /login | Both | Login page |
| /teacher | Teacher | Dashboard redirect |
| /teacher/questions | Teacher | Question list, add/edit, text import |
| /teacher/papers | Teacher | Paper list, create, build exam |
| /teacher/exams | Teacher | Publish/unpublish exams |
| /teacher/submissions | Teacher | View student submissions, grade essays |
| /teacher/grades | Teacher | Score table per paper |
| /student | Student | Redirect to /student/exams |
| /student/exams | Student | Available exam list |
| /student/exam/{id} | Student | Exam taking interface |
| /student/results | Student | Published results list |
| /student/result/{id} | Student | Detailed result view |

### Key Components
- `QuestionRenderer` — renders choice/fill/essay inputs based on question type
- `Timer` — countdown display, triggers callback on expiry
- `NavBar` — role-aware navigation
- `ExamView` — full exam page with one-question-per-screen, prev/next navigation, question number bar, mark-for-review, submit button

### ExamView Layout
```
┌─────────────────────────────────────────────────────┐
│  剩余时间: 45:32          题目 3/20  ▶ [下一题]     │
├─────────────────────────────────────────────────────┤
│  Question content area                                │
│  (rendered by QuestionRenderer)                       │
│                                                       │
├─────────────────────────────────────────────────────┤
│  [◀ 上一题]  [标记]  [1] [2] [3] [4] [5] [6] ...    │
│                        [提交试卷]                     │
└─────────────────────────────────────────────────────┘
```

## 7. Security

- Passwords: bcrypt hashed, never stored in plaintext
- Authentication: JWT bearer tokens, role-checked on every API call
- SQL injection: prevented by SQLAlchemy parameterized queries
- XSS: frontend escapes user input before rendering
- HTTPS: recommended via Nginx reverse proxy + Let's Encrypt for production

## 8. File Structure

```
exam-proj/
├── backend/
│   ├── main.py                  # FastAPI entry
│   ├── config.py                # config (DB path, JWT secret)
│   ├── database.py              # SQLAlchemy engine + session
│   ├── models.py                # DB models
│   ├── schemas.py               # Pydantic schemas
│   ├── auth.py                  # JWT + password hashing
│   ├── routers/
│   │   ├── auth.py
│   │   ├── questions.py
│   │   ├── papers.py
│   │   ├── exams.py
│   │   └── grading.py
│   ├── services/
│   │   ├── question_parser.py   # text file parser
│   │   ├── exam_engine.py       # paper building logic
│   │   └── grading_engine.py    # auto-grading logic
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── main.js
│   │   ├── router.js
│   │   ├── api.js
│   │   ├── auth.js
│   │   ├── views/
│   │   │   ├── Login.vue
│   │   │   ├── student/
│   │   │   │   ├── ExamList.vue
│   │   │   │   ├── ExamView.vue
│   │   │   │   └── Results.vue
│   │   │   └── teacher/
│   │   │       ├── QuestionBank.vue
│   │   │       ├── PaperBuilder.vue
│   │   │       ├── ExamManager.vue
│   │   │       ├── Submissions.vue
│   │   │       └── Grades.vue
│   │   └── components/
│   │       ├── QuestionRenderer.vue
│   │       ├── Timer.vue
│   │       └── NavBar.vue
│   └── dist/                    # built SPA served by FastAPI
└── data/
    └── exam.db                  # SQLite database
```

## 9. Development Phases

1. **Backend foundation** — FastAPI setup, DB models, auth, basic CRUD APIs
2. **QuestionBank** — text parser, question CRUD, import endpoint
3. **PaperBuilder** — paper CRUD, question selection (random + specified)
4. **ExamRunner** — exam session creation, question delivery, answer saving, submission
5. **GradingEngine** — auto-grading, manual essay grading, result publishing
6. **Frontend** — login, teacher pages, student pages, exam view
7. **Integration** — connect frontend to backend, deploy static files
8. **Testing & polish** — end-to-end flows, edge cases
