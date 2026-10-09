"""Pydantic schemas for request/response bodies."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class RegisterIn(BaseModel):
    username: str = Field(min_length=2, max_length=40)
    password: str = Field(min_length=4, max_length=80)
    email: Optional[str] = None

class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str

class ProblemSummary(BaseModel):
    id: int
    title: str
    difficulty: str
    accept_rate: Optional[float] = None
    tags: List[str] = []

class TestCaseIn(BaseModel):
    input: Dict[str, Any]
    expected: Any

class ProblemDetail(BaseModel):
    id: int
    title: str
    difficulty: str
    accept_rate: Optional[float] = None
    tags: List[str] = []
    description: str
    signature: str
    test_cases: List[TestCaseIn] = []

class SubmitIn(BaseModel):
    problem_id: int
    code: str
    language: str = "python"

class SubmitOut(BaseModel):
    submission_id: int
    status: str
    verdict: str
    passed: int
    total: int
    time_ms: int
    memory_kb: int
    detail: Dict[str, Any] = {}

class SubmissionOut(BaseModel):
    id: int
    user_id: int
    problem_id: int
    language: str
    code: str
    status: str
    verdict: str
    passed: int
    total: int
    time_ms: int
    memory_kb: int
    detail: Dict[str, Any]
    created_at: str
