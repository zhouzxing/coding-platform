"""Problem registry: loads problems from a JSON file."""
from __future__ import annotations
import json, os
from functools import lru_cache
from typing import Dict, List, Optional

PROBLEMS_PATH = os.environ.get(
    "CODING_PROBLEMS_PATH",
    os.path.join(os.path.dirname(__file__), "data", "problems.json"),
)


@lru_cache(maxsize=1)
def _load_all() -> Dict[int, dict]:
    with open(PROBLEMS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {p["id"]: p for p in data}


def list_problems() -> List[dict]:
    return list(_load_all().values())


def get_problem(pid):
    return _load_all().get(pid)


def visible_problem_view(p):
    return {
        "id": p["id"],
        "title": p["title"],
        "difficulty": p.get("difficulty", "Medium"),
        "accept_rate": p.get("accept_rate"),
        "tags": p.get("tags", []),
        "description": p.get("description", ""),
        "signature": p.get("signature", "def solve(*args, **kwargs) -> None:"),
        "test_cases": p.get("test_cases", []),
    }
