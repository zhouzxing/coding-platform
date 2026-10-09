"""Judge user code against visible + hidden test cases."""
from __future__ import annotations
from typing import Any
from executor import run_user_code, MEM_LIMIT_MB


def _wrap_input(params):
    return {"params": list(params.values()) if isinstance(params, dict) else [], "kwargs": {}}


def _eq(a, b):
    if isinstance(a, float) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-6
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b): return False
        return all(_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a.keys()) == set(b.keys()) and all(_eq(a[k], b[k]) for k in a)
    return a == b


def _classify(r):
    if r.timed_out: return "TLE", f"Time limit exceeded (>{r.runtime_ms}ms)"
    if r.memory_exceeded: return "MLE", f"Memory limit exceeded (>{r.max_rss_kb} KB, cap {MEM_LIMIT_MB}MB)"
    if r.payload is None: return "CompileError", "Harness could not read user output"
    err = r.payload.get("_error", "")
    if err.startswith("compile:"): return "CompileError", err
    if err.startswith("memory:"): return "MLE", "Memory limit exceeded (MemoryError raised by Python)"
    if err.startswith("runtime:"): return "RuntimeError", err
    if err: return "JudgeError", err
    return "OK", ""


def judge_case(source, case, test_index):
    params = case.get("input", {}) or {}
    inp = _wrap_input(params)
    expected = case.get("expected")
    r = run_user_code(source, inp)
    status, msg = _classify(r)
    got = r.payload.get("result") if r.payload else None
    if status == "OK":
        if _eq(got, expected):
            verdict = "Accepted"
            status = "Accepted"
        else:
            verdict = f"Wrong answer: expected {expected!r}, got {got!r}"
            status = "WrongAnswer"
    else:
        verdict = msg
    return {
        "index": test_index, "input": params, "expected": expected, "got": got,
        "verdict": verdict, "status": status,
        "runtime_ms": r.runtime_ms, "memory_kb": r.max_rss_kb,
        "timed_out": r.timed_out, "memory_exceeded": r.memory_exceeded,
        "exit_code": r.exit_code,
    }


FAIL_STATUS = {"TLE", "MLE", "RuntimeError", "CompileError"}

def judge_all(source, all_cases, *, stop_on_fail: bool = False):
    details = []
    total = len(all_cases)
    for i, c in enumerate(all_cases):
        d = judge_case(source, c, i)
        details.append(d)
        # Short-circuit on fatal failure (TLE / MLE / RTE / CompileError).
        # This saves time when the submission is clearly broken.
        if stop_on_fail and d["status"] in FAIL_STATUS:
            break
    passed = sum(1 for d in details if d["status"] in ("Accepted", "OK"))
    statuses = [d["status"] for d in details]
    if any(s == "TLE" for s in statuses): overall = "TLE"
    elif any(s == "MLE" for s in statuses): overall = "MLE"
    elif any(s == "RuntimeError" for s in statuses): overall = "RuntimeError"
    elif any(s == "CompileError" for s in statuses): overall = "CompileError"
    elif any(s == "WrongAnswer" for s in statuses): overall = "WrongAnswer"
    elif any(s == "JudgeError" for s in statuses): overall = "JudgeError"
    elif passed == total: overall = "Accepted"
    else: overall = "WrongAnswer"
    total_ms = sum(d.get("runtime_ms", 0) for d in details)
    peak_kb = max((d.get("memory_kb", 0) for d in details), default=0)
    verdict = "All tests passed"
    for d in details:
        if d["status"] not in ("Accepted", "OK"):
            verdict = f"Test #{d['index']+1}: {d['verdict']}"
            break
    return {
        "status": overall, "passed": passed, "total": total,
        "time_ms": total_ms, "memory_kb": peak_kb,
        "details": details, "verdict": verdict,
    }
