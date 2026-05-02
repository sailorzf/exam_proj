# backend/main.py (FINAL)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from database import init_db
from routers import auth as auth_router
from routers import questions as questions_router
from routers import papers as papers_router
from routers import exams as exams_router
from routers import grading as grading_router
from routers import users as users_router

app = FastAPI(title="Exam System")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router.router)
app.include_router(questions_router.router)
app.include_router(papers_router.router)
app.include_router(exams_router.router)
app.include_router(grading_router.router)
app.include_router(users_router.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


import os
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if os.environ.get("PRODUCTION") and FRONTEND_DIST.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"error": "Frontend not built"}
