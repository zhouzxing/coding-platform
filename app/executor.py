"""Sandboxed Python code execution."""
from __future__ import annotations
import json, os, resource, subprocess, sys, time
from string import Template
from dataclasses import dataclass
from typing import Optional

TIME_LIMIT_SEC = float(os.environ.get("EXEC_TIMEOUT_SEC", "3.0"))
MEM_LIMIT_MB = int(os.environ.get("EXEC_MEM_MB", "256"))

@dataclass
class RunResult:
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    killed: bool
    runtime_ms: int
    max_rss_kb: int
    memory_exceeded: bool
    payload: Optional[dict]

_HARNESS_TMPL = "\nimport json, sys, os, signal, resource, time\n_MAX_KB = $mem_kb\nresource.setrlimit(resource.RLIMIT_AS, (_MAX_KB*1024, _MAX_KB*1024))\ntry:\n    signal.signal(signal.SIGALRM, signal.SIG_IGN)\nexcept Exception:\n    pass\n_t0 = time.time()\ntry:\n    _INPUT = json.loads(sys.stdin.read() or \"null\")\nexcept Exception as e:\n    print(json.dumps({\"_error\": \"input_parse: \" + repr(e)})); sys.exit(3)\n_ARGS = _INPUT.get(\"params\", []) if isinstance(_INPUT, dict) else []\n_KWARGS = _INPUT.get(\"kwargs\", {}) if isinstance(_INPUT, dict) else {}\n_solve = None\ntry:\n$source\n    _solve = solve\nexcept Exception as e:\n    print(json.dumps({\"_error\": \"compile: \" + type(e).__name__ + \": \" + str(e), \"runtime_ms\": int((time.time()-_t0)*1000)})); sys.exit(3)\nif _solve is None:\n    print(json.dumps({\"_error\": \"compile: user code did not define solve(...)\", \"runtime_ms\": int((time.time()-_t0)*1000)})); sys.exit(3)\ntry:\n    _result = _solve(*_ARGS, **_KWARGS)\nexcept SystemExit as e:\n    print(json.dumps({\"_error\": \"runtime: SystemExit(\" + repr(getattr(e, \"code\", None)) + \"))\"})); sys.exit(3)\nexcept MemoryError as e:\n    print(json.dumps({\"_error\": \"memory: MemoryError: \" + str(e), \"runtime_ms\": int((time.time()-_t0)*1000)})); sys.exit(3)\nexcept Exception as e:\n    print(json.dumps({\"_error\": \"runtime: \" + type(e).__name__ + \": \" + str(e), \"runtime_ms\": int((time.time()-_t0)*1000)})); sys.exit(3)\ntry:\n    _serialized = json.dumps({\"result\": _result})\nexcept Exception as e:\n    print(json.dumps({\"_error\": \"serialize: \" + repr(e)})); sys.exit(3)\ntry:\n    _ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss\nexcept Exception:\n    _ru = 0\nprint(json.dumps({\"result\": _result, \"runtime_ms\": int((time.time()-_t0)*1000), \"max_rss_kb\": int(_ru)}))\nsys.exit(0)\n"

# Indent user code so it can sit inside a try: block. Only indent
# lines that start at column 0 (blank lines are skipped). Relative
# indentation between user lines is preserved.
def _indent_source(src: str) -> str:
    """Indent EVERY line by 4 spaces. This makes the user's code sit
    inside a `try:` block. Since we indent uniformly, relative
    indentation between user lines is preserved exactly."""
    import textwrap
    return textwrap.indent(src, "    ").rstrip("\n")

def run_user_code(source, test_input, *, timeout=None, mem_mb=None):
    timeout = timeout if timeout is not None else TIME_LIMIT_SEC
    mem_mb = mem_mb if mem_mb is not None else MEM_LIMIT_MB
    source = _indent_source(source)
    harness = Template(_HARNESS_TMPL).safe_substitute(source=source, mem_kb=str(mem_mb * 1024))
    stdin_data = json.dumps({"params": test_input.get("params", test_input.get("args", [])), "kwargs": test_input.get("kwargs", {})})
    try:
        proc = subprocess.Popen(
            [sys.executable, "-I", "-c", harness],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            env={"PYTHONIOENCODING": "utf-8", "PATH": "/usr/bin:/bin"},
        )
    except Exception as e:
        return RunResult(False, -1, "", f"spawn failed: {e!r}", False, False, 0, 0, False, None)
    start = time.time()
    timed_out = False
    killed = False
    try:
        stdout, stderr = proc.communicate(input=stdin_data.encode("utf-8"), timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True; killed = True
        try: proc.kill()
        except Exception: pass
        try: stdout, stderr = proc.communicate(timeout=2)
        except Exception: stdout, stderr = b"", b""
    wall_ms = int((time.time() - start) * 1000)
    stdout_s = stdout.decode("utf-8", errors="replace")
    stderr_s = stderr.decode("utf-8", errors="replace")
    payload = None
    for line in stdout_s.splitlines():
        line = line.strip()
        if not line: continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                payload = obj; break
        except Exception:
            continue
    max_rss_kb = int(payload.get("max_rss_kb", 0)) if payload else 0
    return RunResult(
        ok=(proc.returncode == 0 and payload is not None and "_error" not in (payload or {})),
        exit_code=proc.returncode,
        stdout=stdout_s, stderr=stderr_s,
        timed_out=timed_out, killed=killed,
        runtime_ms=int(payload.get("runtime_ms", wall_ms)) if payload else wall_ms,
        max_rss_kb=max_rss_kb,
        memory_exceeded=(max_rss_kb > mem_mb * 1024 * 1.05),
        payload=payload,
    )