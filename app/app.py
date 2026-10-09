"""FastAPI main app: auth + problems + submissions + run endpoints."""
from __future__ import annotations
import json, os
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from auth import hash_password, verify_password, create_token, current_user, JWT_SECRET
from db import User, Submission, get_session
from models import (RegisterIn, LoginIn, TokenOut, ProblemSummary,
                    ProblemDetail, SubmitIn, SubmitOut, SubmissionOut, TestCaseIn)
from problems import list_problems, get_problem, visible_problem_view
from judge import judge_all


def _submission_out(s: Submission) -> SubmissionOut:
    return SubmissionOut(
        id=s.id, user_id=s.user_id, problem_id=s.problem_id, language=s.language,
        code=s.code, status=s.status, verdict=s.verdict,
        passed=s.passed, total=s.total, time_ms=s.time_ms, memory_kb=s.memory_kb,
        detail=json.loads(s.detail or "{}"),
        created_at=(s.created_at.isoformat() + "+00:00") if s.created_at else "",
    )


app = FastAPI(title="Coding Platform", version="1.0.0")
app.add_middleware(CORSMiddleware,
                   allow_origins=os.environ.get("CODING_CORS_ORIGINS", "*").split(","),
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# ---------- Health ----------
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "coding-platform"}


# ---------- Auth ----------
@app.post("/api/auth/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_session)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
    h, salt = hash_password(body.password)
    user = User(username=body.username, password_hash=h, salt=salt, email=body.email)
    db.add(user); db.commit(); db.refresh(user)
    return TokenOut(access_token=create_token(user), user_id=user.id, username=user.username)


@app.post("/api/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_session)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.salt, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    return TokenOut(access_token=create_token(user), user_id=user.id, username=user.username)


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"user_id": user.id, "username": user.username, "email": user.email}


# ---------- Problems ----------
@app.get("/api/problems", response_model=List[ProblemSummary])
def get_problems(
    difficulty: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    items = list_problems()
    if difficulty:
        items = [p for p in items if p.get("difficulty","").lower() == difficulty.lower()]
    if q:
        ql = q.lower()
        items = [p for p in items if ql in p["title"].lower() or any(ql in t.lower() for t in p.get("tags", []))]
    return [ProblemSummary(id=p["id"], title=p["title"], difficulty=p.get("difficulty","Medium"),
                           accept_rate=p.get("accept_rate"), tags=p.get("tags", [])) for p in items]


@app.get("/api/problems/{pid}", response_model=ProblemDetail)
def get_problem_view(pid: int):
    p = get_problem(pid)
    if not p: raise HTTPException(status.HTTP_404_NOT_FOUND, "Problem not found")
    view = visible_problem_view(p)
    return ProblemDetail(
        id=view["id"], title=view["title"], difficulty=view["difficulty"],
        accept_rate=view["accept_rate"], tags=view["tags"],
        description=view["description"], signature=view["signature"],
        test_cases=[TestCaseIn(input=tc["input"], expected=tc["expected"]) for tc in view["test_cases"]],
    )


# ---------- Submissions ----------
@app.post("/api/problems/{pid}/run", response_model=SubmitOut)
def run_problem(pid: int, body: SubmitIn, user: User = Depends(current_user), db: Session = Depends(get_session)):
    """Run hidden tests only. Saves submission record."""
    p = get_problem(pid)
    if not p: raise HTTPException(status.HTTP_404_NOT_FOUND, "Problem not found")
    hidden = p.get("hidden_tests", [])
    if not hidden:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No hidden tests for this problem")
    result = judge_all(body.code, hidden, stop_on_fail=True)
    s = Submission(
        user_id=user.id, problem_id=pid, language=body.language, code=body.code,
        status=result["status"], verdict=result["verdict"],
        passed=result["passed"], total=result["total"],
        time_ms=result["time_ms"], memory_kb=result["memory_kb"],
        detail=json.dumps({"results": result["details"]}),
    )
    db.add(s); db.commit(); db.refresh(s)
    return SubmitOut(
        submission_id=s.id, status=s.status, verdict=s.verdict,
        passed=s.passed, total=s.total, time_ms=s.time_ms, memory_kb=s.memory_kb,
        detail={"results": result["details"]},
    )


@app.post("/api/problems/{pid}/run/visible", response_model=SubmitOut)
def run_visible(pid: int, body: SubmitIn, db: Session = Depends(get_session)):
    """Run only visible tests (for user to iterate locally). Doesn't save."""
    p = get_problem(pid)
    if not p: raise HTTPException(status.HTTP_404_NOT_FOUND, "Problem not found")
    visible = p.get("test_cases", [])
    result = judge_all(body.code, visible, stop_on_fail=True)
    return SubmitOut(
        submission_id=0, status=result["status"], verdict=result["verdict"],
        passed=result["passed"], total=result["total"],
        time_ms=result["time_ms"], memory_kb=result["memory_kb"],
        detail={"results": result["details"]},
    )


@app.get("/api/submissions", response_model=List[SubmissionOut])
def get_submissions(problem_id: Optional[int] = Query(None),
                    user: User = Depends(current_user),
                    db: Session = Depends(get_session)):
    q = db.query(Submission).filter(Submission.user_id == user.id)
    if problem_id is not None:
        q = q.filter(Submission.problem_id == problem_id)
    subs = q.order_by(Submission.id.desc()).limit(100).all()
    return [_submission_out(s) for s in subs]


@app.post("/api/submissions/{sid}/bind", status_code=200)
def bind_submission(sid: int, user: User = Depends(current_user), db: Session = Depends(get_session)):
    """Attach an anonymous run to the current logged-in user."""
    s = db.get(Submission, sid)
    if not s: raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    if s.user_id not in (0, user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot bind another user's submission")
    s.user_id = user.id
    db.commit(); db.refresh(s)
    return {"ok": True}


# ---------- Seed ----------
@app.post("/api/admin/seed-demo-user")
def seed_demo_user(username: str = Query("demo"), password: str = Query("demo1234"),
                   db: Session = Depends(get_session)):
    h, salt = hash_password(password)
    u = db.query(User).filter(User.username == username).first()
    if not u:
        u = User(username=username, password_hash=h, salt=salt)
        db.add(u); db.commit(); db.refresh(u)
    return {"user_id": u.id, "username": u.username}

