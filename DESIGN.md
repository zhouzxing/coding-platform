# Coding Platform — 设计与实现文档

> 在线编程练习平台。从零构建一个类 LeetCode 的刷题系统，支持注册登录、题目浏览、代码编写、沙箱执行与实时判分。

---

## 目录

1. [系统概述](#1-系统概述)
2. [架构总览](#2-架构总览)
3. [后端设计](#3-后端设计)
   - 3.1 模块划分
   - 3.2 数据模型 (ER)
   - 3.3 API 设计
   - 3.4 认证模块
   - 3.5 沙箱执行引擎
   - 3.6 判分系统
   - 3.7 题目管理
4. [前端设计](#4-前端设计)
   - 4.1 技术选型
   - 4.2 路由与页面结构
   - 4.3 状态管理
   - 4.4 核心组件
5. [数据流与时序](#5-数据流与时序)
6. [安全设计](#6-安全设计)
7. [部署与运维](#7-部署与运维)
8. [扩展规划](#8-扩展规划)

---

## 1. 系统概述

### 1.1 目标

构建一个支持以下功能的在线编程平台：

| 能力 | 说明 |
|------|------|
| 用户系统 | 注册 / 登录，JWT 无状态认证 |
| 题目系统 | 6 道经典算法题，难度筛选 + 关键词搜索 |
| 代码编辑 | CodeMirror 6 编辑器，Python 语法高亮 |
| 判分系统 | 可见测试即时运行（可匿名），隐藏测试提交判分（需登录） |
| 提交记录 | 保存每次提交的代码 / 状态 / 通过率 / 耗时 / 内存 |
| 沙箱执行 | subprocess + resource.setrlimit 隔离执行，超时 / 内存 / 异常全兜底 |

### 1.2 技术栈

| 层 | 技术选型 | 版本 |
|----|----------|------|
| 后端框架 | FastAPI | 0.115.0 |
| ASGI 服务器 | Uvicorn (uvloop) | 0.30.6 |
| ORM | SQLAlchemy | 2.0.35 |
| 数据库 | SQLite | 内置 |
| 数据验证 | Pydantic | 2.9.2 |
| 认证 | PyJWT | 2.10.1 |
| 表单解析 | python-multipart | 0.0.18 |
| 前端框架 | React 18 + TypeScript | 18.3.1 / 5.5.3 |
| 构建工具 | Vite | 5.4.0 |
| 代码编辑器 | CodeMirror 6 | 6.0.1 |
| 语法高亮 | @codemirror/lang-python | 6.1.6 |
| 编辑器主题 | @codemirror/theme-one-dark | 6.1.2 |
| Markdown 渲染 | react-markdown | 9.0.1 |
| 前端路由 | react-router-dom | 6.26.0 |

### 1.3 设计原则

- **零依赖外部服务**：SQLite 文件存储，无需 PostgreSQL / Redis
- **进程级隔离**：用户代码在独立子进程中执行，与主进程物理隔离
- **无状态认证**：JWT 签名验证，服务端不存 session
- **前后端分离**：FastAPI 提供 API，React SPA 消费，Vite 代理解决跨域
- **配置即环境变量**：所有可变参数通过 `CODING_*` 环境变量注入

---

## 2. 架构总览

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         浏览器 (用户端)                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  React SPA (Vite dev server :5173 / Nginx 生产部署)       │  │
│  │  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐  │  │
│  │  │ Home     │ │ Problems │ │ Editor    │ │ Login/Reg │  │  │
│  │  │ 落地页   │ │ 题目列表  │ │ 代码编辑器 │ │ 认证页    │  │  │
│  │  └─────────┘ └──────────┘ └───────────┘ └───────────┘  │  │
│  │       │              │              │            │       │  │
│  │       └──────────────┴──────┬───────┴────────────┘       │  │
│  │                             │                             │  │
│  │                    api.ts (fetch client)                   │  │
│  │                    AuthContext (JWT 管理)                  │  │
│  └─────────────────────────────┬─────────────────────────────┘  │
└────────────────────────────────┼────────────────────────────────┘
                                 │ HTTP (JSON)
                                 │ /api/*  (Vite proxy → :8001)
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI 后端 (:8001)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  CORSMiddleware                                          │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Router Layer                                             │   │
│  │  /api/health          /api/auth/*      /api/problems/*   │   │
│  │  /api/submissions     /api/admin/*                        │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Business Layer                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │   │
│  │  │ auth.py  │  │ judge.py │  │ problems  │  │ db.py  │ │   │
│  │  │ JWT+Hash │  │ 判分引擎  │  │ .py 题库  │  │ ORM   │ │   │
│  │  └──────────┘  └────┬─────┘  └──────────┘  └────────┘ │   │
│  │                  ┌───┴───┐                               │   │
│  │          ┌───────┴───┐   │                               │   │
│  │          │ executor  │   │                               │   │
│  │          │ .py       │   │                               │   │
│  │          │ 沙箱执行   │   │                               │   │
│  │          └───────┬───┘   │                               │   │
│  │                  │       │                               │   │
│  │            subprocess   resource.setrlimit              │   │
│  └──────────────────┬─────────────────────────────────────┘   │
└─────────────────────┼─────────────────────────────────────────┘
                      │
           ┌──────────┴──────────┐
           │   持久层             │
           │  ┌───────────────┐  │
           │  │ SQLite        │  │
           │  │ coding.db     │  │
           │  │ (users +      │  │
           │  │  submissions) │  │
           │  └───────────────┘  │
           │  ┌───────────────┐  │
           │  │ problems.json │  │
           │  │ (静态题库)     │  │
           │  └───────────────┘  │
           └─────────────────────┘
```

### 2.2 请求流转路径

```
浏览器
  │
  │ fetch("/api/problems/:id/run", { body: { code, language } })
  ▼
Vite Dev Server (:5173)
  │  proxy: /api → http://127.0.0.1:8001
  ▼
FastAPI (:8001)
  │  1. CORSMiddleware → CORS 校验
  │  2. current_user dep → JWT 解码 → 查 User
  │  3. get_problem(pid) → 从 problems.json 读题
  │  4. judge_all(code, hidden_tests)
  │     │
  │     ▼
  │  judge.py
  │     │  for each test_case:
  │     │    _wrap_input → run_user_code
  │     │      │
  │     │      ▼
  │     │  executor.py
  │     │    subprocess.Popen([python -I, -c, harness])
  │     │    stdin: {"params": [...], "kwargs": {...}}
  │     │    resource.setrlimit(RLIMIT_AS, 256MB)
  │     │    proc.communicate(timeout=3.0)
  │     │    stdout: {"result": ..., "runtime_ms": ..., "max_rss_kb": ...}
  │     │      │
  │     │      ▼
  │     │  比对 result == expected → Accepted / WrongAnswer
  │     │
  │     ▼
  │  汇总 → Submission 记录 → 写入 SQLite
  │
  ▼
返回 JSON: { submission_id, status, verdict, passed, total, time_ms, ... }
```

---

## 3. 后端设计

### 3.1 模块划分

```
app/
├── app.py          # FastAPI 入口 + 全部路由 + 依赖注入
├── auth.py         # 密码哈希 + JWT 签发/校验 + current_user 依赖
├── db.py           # SQLAlchemy engine + ORM 模型 + get_session 依赖
├── models.py       # Pydantic 请求/响应 schema
├── executor.py     # 沙箱执行引擎（subprocess + harness）
├── judge.py        # 判分逻辑（比对 + 状态分类 + 汇总）
├── problems.py     # 题目加载器（从 JSON 文件读取，lru_cache 缓存）
└── data/
    ├── coding.db       # SQLite（自动创建）
    ├── problems.json   # 题库（seed_problems.py 生成）
    └── seed_problems.py
```

各模块依赖关系：

```
app.py
 ├── auth.py  (JWT, 密码哈希, current_user)
 │    └── db.py  (User 模型, get_session)
 ├── models.py  (Pydantic schemas)
 ├── problems.py  (题库加载)
 │    └── data/problems.json
 ├── judge.py  (判分)
 │    └── executor.py  (沙箱)
 └── db.py  (Submission 模型, get_session)
```

### 3.2 数据模型 (ER)

```
┌──────────────────────────────┐          ┌──────────────────────────────────┐
│          users               │          │          submissions              │
├──────────────────────────────┤          ├──────────────────────────────────┤
│ id          PK, AUTOINCREMENT│          │ id          PK, AUTOINCREMENT    │
│ username    VARCHAR(40) UNIQUE│  1:N   │ user_id     FK → users.id (CASCADE)│
│ password_hash VARCHAR(128)  │◄───────│ problem_id  INT (indexed)         │
│ salt        VARCHAR(16)      │          │ language    VARCHAR(20) default   │
│ email       VARCHAR(120) NULL│          │ code        TEXT                  │
│ created_at  DATETIME (UTC)   │          │ status      VARCHAR(20)          │
└──────────────┬───────────────┘          │ verdict     VARCHAR(200)          │
               │                            │ passed      INT                  │
               │                            │ total       INT                  │
               │                            │ time_ms     INT                  │
               │                            │ memory_kb   INT                  │
               │                            │ detail      TEXT (JSON string)   │
               │                            │ created_at  DATETIME (UTC)       │
               │                            └──────────────────────────────────┘
               │
               │  relationship: submissions (back_populates="user")
               ▼
        User.submissions → [Submission, ...]
        Submission.user → User
```

**设计要点：**

- **外键 + CASCADE 删除**：删除用户时自动清理其提交记录。SQLite 默认关闭外键约束，通过 `event.listens_for(engine, "connect")` 注入 `PRAGMA foreign_keys=ON`。
- **索引**：`username` (唯一索引，快速登录查找)、`user_id` (提交记录按用户查询)、`problem_id` (按题目查提交)。
- **detail 字段**：以 JSON 字符串存储每条测试用例的详细结果（index / input / expected / got / verdict / runtime / memory），前端反序列化后渲染。

**problems.json (题库) 结构：**

```json
{
  "id": 1,
  "title": "Two Sum",
  "difficulty": "Easy",          // Easy | Medium | Hard
  "accept_rate": 55.2,           // 静态字段，非实时计算
  "tags": ["Array", "Hash Map"],
  "description": "## 题目\n\nMarkdown 题面...",
  "signature": "def solve(nums: list[int], target: int) -> list[int]:",
  "test_cases": [                // 可见测试（用户可见 + 可运行）
    {"input": {"nums": [2,7,11,15], "target": 9}, "expected": [0,1]}
  ],
  "hidden_tests": [              // 隐藏测试（提交后运行，用户不可见）
    {"input": {"nums": [3,2,4], "target": 6}, "expected": [1,2]}
  ]
}
```

题库是静态 JSON 文件，通过 `problems.py` 的 `lru_cache(maxsize=1)` 加载，进程生命周期内不重新读取。

### 3.3 API 设计

#### 3.3.1 端点总览

| Method | Path | 认证 | 说明 |
|--------|------|------|------|
| GET | `/api/health` | 无 | 健康检查，返回 `{"status":"ok"}` |
| POST | `/api/auth/register` | 无 | 注册，返回 JWT |
| POST | `/api/auth/login` | 无 | 登录，返回 JWT |
| GET | `/api/auth/me` | JWT | 当前用户信息 |
| GET | `/api/problems` | 无 | 题目列表，支持 `difficulty` / `q` 筛选 |
| GET | `/api/problems/{pid}` | 无 | 题目详情（含可见测试，不含隐藏测试） |
| POST | `/api/problems/{pid}/run/visible` | 无 | 运行可见测试（不保存记录） |
| POST | `/api/problems/{pid}/run` | JWT | 运行隐藏测试 + 保存提交记录 |
| GET | `/api/submissions` | JWT | 当前用户提交记录，支持 `problem_id` 过滤 |
| POST | `/api/submissions/{sid}/bind` | JWT | 将匿名提交绑定到当前用户 |
| POST | `/api/admin/seed-demo-user` | 无 | 创建演示用户（开发辅助） |

#### 3.3.2 请求/响应 Schema

**认证**

```python
# 注册请求
class RegisterIn(BaseModel):
    username: str    # 2-40 字符
    password: str    # 4-80 字符
    email: Optional[str] = None

# 登录请求
class LoginIn(BaseModel):
    username: str
    password: str

# Token 响应
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
```

**题目**

```python
class ProblemSummary(BaseModel):     # 列表项
    id: int
    title: str
    difficulty: str
    accept_rate: Optional[float] = None
    tags: List[str] = []

class TestCaseIn(BaseModel):        # 单个测试用例
    input: Dict[str, Any]
    expected: Any

class ProblemDetail(BaseModel):      # 详情（含可见测试）
    id: int
    title: str
    difficulty: str
    accept_rate: Optional[float] = None
    tags: List[str] = []
    description: str                # Markdown
    signature: str                  # 函数签名
    test_cases: List[TestCaseIn] = []
    # hidden_tests 不在响应中 — 安全隔离
```

**判分**

```python
class SubmitIn(BaseModel):
    problem_id: int
    code: str
    language: str = "python"        # 预留多语言扩展

class SubmitOut(BaseModel):
    submission_id: int              # 0 = 未保存（visible run）
    status: str                     # Accepted | WrongAnswer | TLE | ...
    verdict: str                    # 人类可读判分描述
    passed: int
    total: int
    time_ms: int                    # 所有用例累计耗时
    memory_kb: int                  # 所有用例峰值内存
    detail: Dict[str, Any]          # {"results": [TestCaseResult, ...]}
```

**提交记录**

```python
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
    created_at: str                 # ISO 8601
```

#### 3.3.3 路由实现细节

**依赖注入模式**

FastAPI 通过 `Depends()` 实现依赖链式注入：

```python
@app.post("/api/problems/{pid}/run")
def run_problem(
    pid: int,
    body: SubmitIn,
    user: User = Depends(current_user),   # JWT → User
    db: Session = Depends(get_session),    # DB session
):
    ...
```

`current_user` 依赖自身的依赖链：

```
current_user
  ├── _bearer = HTTPBearer(auto_error=False)  → 提取 Authorization header
  └── get_session()                           → DB session
```

**题目筛选逻辑**

```python
# difficulty: 不区分大小写精确匹配
# q: 标题 OR tags 中包含关键词（不区分大小写）
if difficulty:
    items = [p for p in items if p["difficulty"].lower() == difficulty.lower()]
if q:
    ql = q.lower()
    items = [p for p in items if ql in p["title"].lower()
             or any(ql in t.lower() for t in p.get("tags", []))]
```

**可见测试 vs 隐藏测试的路由设计**

| 路径 | 测试集 | 认证 | 持久化 |
|------|--------|------|--------|
| `/run/visible` | `test_cases` (可见) | 无 | 不保存 |
| `/run` | `hidden_tests` (隐藏) | JWT | 保存到 submissions 表 |

设计意图：用户可以在未登录状态下用可见测试调试代码（Run 按钮），只有提交时才需要登录并运行隐藏测试集（Submit 按钮）。这种分离让用户在"试水"阶段无门槛，在"提交"阶段有身份可追溯。

### 3.4 认证模块 (auth.py)

#### 3.4.1 密码哈希

采用 **SHA-256 + 随机 salt** 方案：

```python
def hash_password(password: str, salt: Optional[str] = None):
    if salt is None:
        salt = secrets.token_hex(8)   # 16 位随机 hex
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return h, salt
```

- **salt 生成**：`secrets.token_hex(8)` — 加密安全随机数生成器
- **哈希计算**：`SHA-256(salt + password)` — salt 前置拼接
- **验证**：`secrets.compare_digest(h, expected_hash)` — 常量时间比较，防时序攻击

> **安全说明**：SHA-256+salt 适用于教学/Demo 场景。生产环境应替换为 bcrypt / argon2（自适应哈希），抵抗暴力破解。

#### 3.4.2 JWT 签发与校验

```python
JWT_SECRET = os.environ.get("CODING_JWT_SECRET", "dev-secret-change-me")
JWT_ALG = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天

def create_token(user: User) -> str:
    payload = {
        "sub": str(user.id),          # subject: 用户 ID
        "username": user.username,
        "exp": datetime.utcnow().timestamp() + JWT_EXPIRE_MINUTES * 60,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
```

- **算法**：HS256（对称密钥），服务端同时签发和验证
- **过期**：7 天，通过 `exp` claim 实现，PyJWT 自动校验过期
- **校验流程**：`HTTPBearer` 提取 `Authorization: Bearer <token>` → `jwt.decode` → 从 `sub` 取 `user_id` → 查 DB → 返回 `User`

#### 3.4.3 FastAPI 依赖注入链

```python
_bearer = HTTPBearer(auto_error=False)   # auto_error=False: 缺 token 不自动 403

def current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_session),
) -> User:
    if creds is None:
        raise HTTPException(401, "Not authenticated")
    data = decode_token(creds.credentials)   # JWT decode + exp 校验
    user_id = int(data.get("sub", 0))
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(401, "User not found")
    return user
```

`auto_error=False` 是关键设计：让 `current_user` 依赖自己决定 401 响应体格式，而不是 FastAPI 的默认 403。这样前端能区分"未登录"和"资源不存在"。

### 3.5 沙箱执行引擎 (executor.py)

这是系统的核心安全组件，负责在隔离环境中执行用户提交的 Python 代码。

#### 3.5.1 执行架构

```
FastAPI 主进程 (judge.py)
    │
    │  run_user_code(source, test_input)
    ▼
executor.py
    │
    │  1. _indent_source(source) — 将用户代码缩进 4 空格，嵌入 harness 的 try 块
    │  2. Template(_HARNESS_TMPL).safe_substitute(source=..., mem_kb=...)
    │  3. 构造 stdin 数据: {"params": [...], "kwargs": {...}}
    │
    ▼
subprocess.Popen([
    sys.executable,    # Python 解释器路径
    "-I",              # 隔离模式：不读 PYTHONPATH / site-packages / .pth
    "-c", harness      # 执行内联 harness 脚本（含用户代码）
], stdin=PIPE, stdout=PIPE, stderr=PIPE,
   close_fds=True,                    # 关闭继承的文件描述符
   env={"PYTHONIOENCODING": "utf-8", "PATH": "/usr/bin:/bin"})  # 最小环境变量
    │
    │  proc.communicate(input=stdin_data, timeout=3.0)
    │
    ▼
子进程内 (harness 脚本执行)
    │
    │  1. resource.setrlimit(RLIMIT_AS, 256MB)  — 设置虚拟内存上限
    │  2. signal.signal(SIGALRM, SIG_IGN)       — 屏蔽 SIGALRM
    │  3. json.loads(sys.stdin.read())          — 读取测试输入
    │  4. exec(用户代码)                         — 执行用户代码，定义 solve 函数
    │  5. result = solve(*args, **kwargs)        — 调用用户函数
    │  6. json.dumps({"result": result, ...})   — 序列化结果
    │  7. print(json_output)                    — 输出到 stdout
    │
    ▼
主进程读取 stdout
    │  解析 JSON payload → RunResult
    │  检查 _error 字段 → 判断编译/运行时/内存错误
    │  检查 max_rss_kb → 判断内存超限
    │
    ▼
返回 RunResult
```

#### 3.5.2 Harness 模板详解

Harness 是一段动态生成的 Python 脚本，将用户代码嵌入受控的 try-catch 框架中：

```python
# harness 执行流程（伪代码）:

# 1. 设置资源限制
_MAX_KB = <mem_kb>
resource.setrlimit(resource.RLIMIT_AS, (_MAX_KB*1024, _MAX_KB*1024))

# 2. 屏蔽信号（防止用户劫持 SIGALRM 绕过超时）
signal.signal(signal.SIGALRM, signal.SIG_IGN)

# 3. 读取输入
_t0 = time.time()
_INPUT = json.loads(sys.stdin.read())
_ARGS = _INPUT.get("params", [])
_KWARGS = _INPUT.get("kwargs", {})

# 4. 执行用户代码（嵌入 try 块捕获编译错误）
try:
    <缩进后的用户代码>    # 定义 solve 函数
    _solve = solve
except Exception as e:
    print({"_error": "compile: ..."})
    sys.exit(3)

# 5. 调用 solve
try:
    _result = _solve(*_ARGS, **_KWARGS)
except SystemExit as e:
    print({"_error": "runtime: SystemExit(...)"})
except MemoryError as e:
    print({"_error": "memory: MemoryError: ..."})
except Exception as e:
    print({"_error": "runtime: ..."})
    sys.exit(3)

# 6. 序列化输出
try:
    _serialized = json.dumps({"result": _result})
except Exception as e:
    print({"_error": "serialize: ..."})

# 7. 上报资源使用
_ru = resource.getrusage(RUSAGE_SELF).ru_maxrss
print({"result": _result, "runtime_ms": ..., "max_rss_kb": ...})
```

**关键设计决策：**

| 决策 | 理由 |
|------|------|
| `python -I` 隔离模式 | 阻止用户通过 `PYTHONSTARTUP` / `.pth` / `sitecustomize.py` 注入代码 |
| `close_fds=True` | 关闭从父进程继承的文件描述符，防止用户代码操作后端文件 |
| 最小 `env` (仅 `PATH` + `PYTHONIOENCODING`) | 阻止通过环境变量泄露信息或注入模块 |
| `RLIMIT_AS` 虚拟地址空间限制 | 比 `RLIMIT_DATA` 更全面：覆盖堆 + mmap + 线程栈 |
| `SIGALRM → SIG_IGN` | 防止用户注册 SIGALRM handler 绕过父进程超时机制 |
| stdin/stdout JSON 协议 | 避免用户代码的 print 干扰结果传输 |
| 输出解析取**最后一个 JSON 行** | 允许用户代码自由 print，harness 的 JSON 行是最后输出 |
| `_indent_source` 统一缩进 | 将用户代码嵌入 `try:` 块，保留相对缩进 |

#### 3.5.3 超时与内存限制

```python
TIME_LIMIT_SEC = float(os.environ.get("EXEC_TIMEOUT_SEC", "3.0"))
MEM_LIMIT_MB = int(os.environ.get("EXEC_MEM_MB", "256"))
```

| 限制 | 实现层 | 机制 | 超限行为 |
|------|--------|------|----------|
| CPU 超时 | 父进程 | `proc.communicate(timeout=3.0)` → `proc.kill()` | 子进程 SIGKILL，`timed_out=True` |
| 内存超限 | 子进程内 | `resource.setrlimit(RLIMIT_AS, 256MB)` | 内存分配失败 → MemoryError |
| 内存超限（兜底） | 父进程 | `max_rss_kb > mem_mb * 1024 * 1.05` | `memory_exceeded=True`（5% 容差） |

双层内存检测：子进程内 `setrlimit` 是硬限制（内核 OOM），父进程检查 `ru_maxrss` 是软检测（对 setrlimit 失效时的兜底）。

#### 3.5.4 RunResult 数据结构

```python
@dataclass
class RunResult:
    ok: bool              # 成功执行且无错误
    exit_code: int       # 子进程退出码（0=正常, 3=harness错误, -9=SIGKILL）
    stdout: str           # 原始 stdout
    stderr: str           # 原始 stderr
    timed_out: bool       # 是否 CPU 超时
    killed: bool          # 是否被 SIGKILL
    runtime_ms: int       # 用户代码执行耗时（子进程上报）
    max_rss_kb: int       # 峰值物理内存（ru_maxrss）
    memory_exceeded: bool # 内存超限
    payload: Optional[dict]  # 解析后的 JSON 输出（含 result / _error）
```

### 3.6 判分系统 (judge.py)

#### 3.6.1 判分流程

```
judge_all(source, all_cases, stop_on_fail)
    │
    │  for i, case in enumerate(all_cases):
    │      │
    │      ▼
    │  judge_case(source, case, i)
    │      │
    │      │  1. _wrap_input(case["input"])
    │      │     → {"params": [val1, val2, ...], "kwargs": {}}
    │      │     将 dict.values() 转为位置参数列表
    │      │
    │      │  2. run_user_code(source, wrapped_input)
    │      │     → RunResult
    │      │
    │      │  3. _classify(result)
    │      │     根据 timed_out / memory_exceeded / payload._error
    │      │     → (status, message)
    │      │
    │      │  4. 如果 status == "OK":
    │      │       _eq(result, expected)
    │      │       → "Accepted" 或 "WrongAnswer"
    │      │
    │      ▼
    │  {index, input, expected, got, verdict, status, runtime_ms, memory_kb, ...}
    │
    │  如果 stop_on_fail 且 status ∈ {TLE, MLE, RTE, CompileError}:
    │      break — 短路退出，不再跑后续用例
    │
    ▼
汇总结果:
    - overall status (优先级: TLE > MLE > RTE > CompileError > WA > Accepted)
    - passed / total
    - time_ms = Σ 各用例耗时
    - memory_kb = max(各用例峰值内存)
    - verdict = 首个失败用例的描述 / "All tests passed"
```

#### 3.6.2 结果比对 (_eq)

支持递归深度比较，处理 Python 类型差异：

```python
def _eq(a, b):
    # 浮点容差: 1e-6
    if isinstance(a, float) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-6
    # 列表/元组递归比较（允许 list == tuple）
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    # 字典递归比较
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a.keys()) == set(b.keys()) and all(_eq(a[k], b[k]) for k in a)
    # 其他类型直接 ==
    return a == b
```

#### 3.6.3 状态分类 (_classify)

```python
def _classify(r: RunResult):
    if r.timed_out:          return "TLE", "Time limit exceeded"
    if r.memory_exceeded:     return "MLE", "Memory limit exceeded"
    if r.payload is None:     return "CompileError", "Harness could not read output"
    err = r.payload.get("_error", "")
    if err.startswith("compile:"):  return "CompileError", err
    if err.startswith("memory:"):   return "MLE", "MemoryError raised"
    if err.startswith("runtime:"):  return "RuntimeError", err
    if err:                          return "JudgeError", err
    return "OK", ""    # 执行成功，等待结果比对
```

#### 3.6.4 判分状态优先级

```python
# 汇总时，按严重性排序取最高优先级错误:
if any(TLE):            overall = "TLE"
elif any(MLE):          overall = "MLE"
elif any(RuntimeError): overall = "RuntimeError"
elif any(CompileError): overall = "CompileError"
elif any(WrongAnswer):  overall = "WrongAnswer"
elif any(JudgeError):   overall = "JudgeError"
elif all passed:        overall = "Accepted"
else:                   overall = "WrongAnswer"
```

#### 3.6.5 短路策略

```python
FAIL_STATUS = {"TLE", "MLE", "RuntimeError", "CompileError"}

for i, c in enumerate(all_cases):
    d = judge_case(source, c, i)
    details.append(d)
    if stop_on_fail and d["status"] in FAIL_STATUS:
        break   # 致命错误，不再跑后续用例
```

只对**致命错误**短路（代码本身就跑不了），对 WrongAnswer 不短路（因为不同用例可能因不同原因失败，全部跑完更有诊断价值）。

### 3.7 题目管理 (problems.py)

#### 3.7.1 加载与缓存

```python
@lru_cache(maxsize=1)
def _load_all() -> Dict[int, dict]:
    with open(PROBLEMS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {p["id"]: p for p in data}
```

- `lru_cache(maxsize=1)` 确保进程生命周期内只读一次 JSON 文件
- 以 `id → dict` 的映射存储，O(1) 查找
- 如需热更新，调用 `_load_all.cache_clear()`

#### 3.7.2 可见视图过滤

```python
def visible_problem_view(p):
    return {
        "id": p["id"],
        "title": p["title"],
        ...
        "test_cases": p.get("test_cases", []),
        # hidden_tests 不在返回中
    }
```

`visible_problem_view` 确保隐藏测试用例不会通过 API 泄露给前端。

---

## 4. 前端设计

### 4.1 技术选型

| 选型 | 理由 |
|------|------|
| React 18 + TypeScript | 类型安全，生态成熟，StrictMode 提前暴露问题 |
| Vite | 极快 HMR，零配置 TypeScript + React 插件 |
| CodeMirror 6 | 模块化、轻量、官方 Python 语言包，比 Monaco 更适合嵌入 |
| react-markdown | 安全的 Markdown 渲染（无 dangerouslySetInnerHTML） |
| react-router-dom v6 | 声明式路由，嵌套路由 |

### 4.2 路由与页面结构

```
/                 → Home          (落地页，功能介绍)
/login            → Login         (登录)
/register         → Register      (注册)
/problems        → Problems      (题目列表 + 筛选 + 搜索)
/problems/:id    → Editor        (题目详情 + 代码编辑器 + 判分结果 + 提交记录)
```

所有页面共享一个 `<Header>` 组件（导航 + 用户状态）。路由在 `App.tsx` 中声明：

```tsx
<Header />
<Routes>
  <Route path="/" element={<Home />} />
  <Route path="/login" element={<Login />} />
  <Route path="/register" element={<Register />} />
  <Route path="/problems" element={<Problems />} />
  <Route path="/problems/:id" element={<Editor />} />
</Routes>
```

### 4.3 状态管理

采用 **React Context** 方案（不引入 Redux / Zustand）：

```
AuthProvider (context/AuthContext.tsx)
    │
    ├── state: { user, loading }
    ├── actions: { login, register, logout }
    ├── 持久化: localStorage (token, username)
    └── 初始化: useEffect → api.me() 验证 token 有效性
```

**AuthContext 工作流程：**

```
App mount
  │
  ▼
AuthProvider useEffect
  │
  ├── localStorage 有 token?
  │     ├── Yes → api.me() → setUser / 失败则清除 token
  │     └── No  → loading=false
  │
  ▼
Header 根据 user 状态渲染:
  - user 存在 → 显示用户名 + Logout
  - user 为空 → 显示 Login + Register
  - loading   → 显示 "..."
```

Token 管理策略：

- `api.ts` 的 `authHeader()` 从 `localStorage.getItem("token")` 读取
- 每次需要认证的请求自动附加 `Authorization: Bearer <token>`
- Token 过期 → API 返回 401 → 前端 catch → 清除 token

### 4.4 核心组件

#### 4.4.1 CodeEditor (CodeMirror 6 封装)

```tsx
export default function CodeEditor({ value, onChange, readOnly }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;   // 避免重建 editor 实例

  useEffect(() => {
    // 创建 CodeMirror 实例
    const state = EditorState.create({
      doc: value,
      extensions: [basicSetup, python(), oneDark, updateListener],
    });
    const view = new EditorView({ state, parent: ref.current });
    viewRef.current = view;
    return () => view.destroy();
  }, []);

  // 外部 value 变化 → 同步到 editor
  useEffect(() => {
    if (viewRef.current && cur !== value) {
      viewRef.current.dispatch({ changes: { from: 0, to: cur.length, insert: value } });
    }
  }, [value]);
}
```

**设计要点：**
- `onChangeRef` 模式：onChange 回调变化时不重建 editor，避免光标跳转
- 外部 value 变化时 dispatch 更新（如 Reset 按钮重置代码）
- 编辑器实例暴露到 `window.__cmEditors` 以支持外部测试

#### 4.4.2 TestPanel (测试结果展示)

渲染单次 Run/Submit 的判分结果：

```
┌──────────────────────────────────────────────────────────┐
│  Hidden Tests                              [ACCEPTED]   │
├──────────────────────────────────────────────────────────┤
│  4 / 5 passed    Time: 120 ms    Mem: 12.3 MB          │
│  Test #5: Wrong answer                                   │
├──────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────┐  │
│  │ Test #1                        [ACCEPTED]         │  │
│  │ input: {"nums": [3,2,4], ...}                      │  │
│  │ ✓ Passed                                           │  │
│  │ 15 ms / 8.2 MB                                     │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Test #5                        [WRONGANSWER]      │  │
│  │ input: {"nums": [0,4,3,0], ...}                    │  │
│  │ expected: [0,3]                                    │  │
│  │ got: [0,3]  ← 红色                                 │  │
│  │ Wrong answer: expected [0,3], got [0,3]            │  │
│  │ 18 ms / 9.1 MB                                     │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

状态颜色映射：
- Accepted → 绿色 (`#1b3025` / `#238636`)
- WrongAnswer → 红色 (`#3d1517` / `#da3633`)
- TLE / MLE → 黄色 (`#3a2a13` / `#9e6a03`)
- RuntimeError → 紫色 (`#2b1a3a` / `#a371f7`)
- CompileError → 淡紫 (`#231427` / `#bc8cff`)

#### 4.4.3 SubmissionList (提交记录列表)

```
┌──────┬─────────────┬─────────┬────────┬──────────────────┐
│  #   │ Status      │ Passed  │ Time   │ When             │
├──────┼─────────────┼─────────┼────────┼──────────────────┤
│ 12   │ [ACCEPTED]  │ 5/5     │ 45 ms  │ 2024-01-15 14:30 │
│ 11   │ [WRONGANS]  │ 3/5     │ 38 ms  │ 2024-01-15 14:28 │
└──────┴─────────────┴─────────┴────────┴──────────────────┘
```

#### 4.4.4 Editor 页面 (核心交互)

Editor 是最复杂的页面，整合了题目展示、代码编辑、判分结果和提交历史：

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back   1. Two Sum  [EASY]  55.2% accepted                    │
│                                    [▶ Run Visible] [✓ Submit]   │
├──────────────────────────┬──────────────────────────────────────┤
│  Problem                 │  Python Editor              [Reset] │
│  ┌─────────────────────┐ │  ┌────────────────────────────────┐│
│  │ ## 题目              │ │  │ def solve(nums, target):       ││
│  │ 给定一个整数数组...   │ │  │     pass                       ││
│  │                      │ │  │                                ││
│  │ ## 示例              │ │  │                                ││
│  │ nums = [2,7,11,15]   │ │  │                                ││
│  │                      │ │  │                                ││
│  │ Tags: [Array] [Hash] │ │  └────────────────────────────────┘│
│  │                      │ │  ┌────────────────────────────────┐│
│  │ ┌─ Visible Tests ──┐│ │  │ Hidden Tests                   ││
│  │ │ 1/1 [ACCEPTED]    ││ │  │ 5/5 [ACCEPTED]  120ms  12.3MB ││
│  │ │ ✓ Test #1 passed  ││ │  │ ✓ Test #1 passed              ││
│  │ └───────────────────┘│ │  │ ✓ Test #2 passed              ││
│  │                      │ │  │ ...                           ││
│  └──────────────────────┘ │  └────────────────────────────────┘│
├──────────────────────────┴──────────────────────────────────────┤
│  My Submissions                                                 │
│  # | Status | Passed | Time | When                             │
│  12 | [AC]   | 5/5     | 45ms | ...                             │
└─────────────────────────────────────────────────────────────────┘
```

布局采用 CSS Grid `1fr 1fr`，左栏题目+可见测试，右栏编辑器+隐藏测试。移动端折叠为单列。

---

## 5. 数据流与时序

### 5.1 提交流程时序图

```
用户      浏览器(SPA)      Vite Proxy      FastAPI         executor         SQLite
 │           │                │               │                │              │
 │  输入代码  │                │               │                │              │
 │──────────►│                │               │                │              │
 │           │                │               │                │              │
 │  点击     │                │               │                │              │
 │  Submit   │                │               │                │              │
 │──────────►│ POST /api/problems/1/run       │                │              │
 │           │ {code: "def solve...", ...}    │                │              │
 │           │───────────────►│               │                │              │
 │           │                │──────────────►│                │              │
 │           │                │               │                │              │
 │           │                │  1. current_user(JWT)           │              │
 │           │                │  2. get_problem(1)              │              │
 │           │                │  3. judge_all(code, hidden)     │              │
 │           │                │               │                │              │
 │           │                │               │  for each test:              │
 │           │                │               │──── run_user_code ──►│        │
 │           │                │               │               subprocess     │
 │           │                │               │               setrlimit       │
 │           │                │               │               communicate     │
 │           │                │               │◄─── RunResult ─────────│        │
 │           │                │               │  _eq(result, expected)      │
 │           │                │               │                │              │
 │           │                │  4. 创建 Submission row          │              │
 │           │                │               │──────────────────────────────►│
 │           │                │               │  INSERT INTO submissions      │
 │           │                │               │◄──────────────────────────────│
 │           │                │               │                │              │
 │           │                │◄──────────────│  SubmitOut JSON │              │
 │           │◄───────────────│               │                │              │
 │           │                │               │                │              │
 │           │  渲染 TestPanel │               │                │              │
 │           │  + SubmissionList               │                │              │
 │◄──────────│                │               │                │              │
 │  显示结果  │                │               │                │              │
```

### 5.2 认证流程时序图

```
用户      浏览器         FastAPI      SQLite
 │           │               │            │
 │  注册/登录 │               │            │
 │──────────►│ POST /api/auth/register    │
 │           │ {username, password}        │
 │           │──────────────►│            │
 │           │               │ hash_password()
 │           │               │──────► INSERT User
 │           │               │◄────── user.id
 │           │               │ create_token(user) → JWT
 │           │◄──────────────│ TokenOut   │
 │           │               │            │
 │           │ localStorage.setItem("token", jwt)         │
 │           │ AuthContext.setUser(user)                  │
 │           │               │            │
 │  跳转 /problems          │            │
 │◄──────────│               │            │
 │           │               │            │
 │  页面加载   │ GET /api/problems        │
 │           │ Authorization: Bearer <jwt>│
 │           │──────────────►│            │
 │           │               │ current_user()
 │           │               │  decode JWT → user_id
 │           │               │  db.get(User, user_id) ──────►│
 │           │               │◄────── User ──────────────────│
 │           │◄──────────────│ [Problem, ...] │
 │           │               │            │
 │  渲染题目列表             │            │
 │◄──────────│               │            │
```

### 5.3 沙箱执行时序

```
judge.py              executor.py              subprocess (python -I)
    │                      │                          │
    │  judge_case()        │                          │
    │  _wrap_input()       │                          │
    │─────────────────────►│                          │
    │                      │  _indent_source(src)     │
    │                      │  Template.substitute()   │
    │                      │  json.dumps(stdin)        │
    │                      │                          │
    │                      │  Popen([python, -I, ...]) │
    │                      │─────────────────────────►│
    │                      │                          │
    │                      │  proc.communicate(       │
    │                      │    input=stdin,          │
    │                      │    timeout=3.0)           │
    │                      │                          │
    │                      │          ┌───────────────┤
    │                      │          │ setrlimit()   │
    │                      │          │ SIGALRM→IGN   │
    │                      │          │ json.loads()  │
    │                      │          │ exec(用户代码)  │
    │                      │          │ solve(*args) │
    │                      │          │ json.dumps()  │
    │                      │          │ print(output)│
    │                      │          └───────────────┤
    │                      │◄─────────────────────────│
    │                      │  stdout, stderr, rc       │
    │                      │                          │
    │                      │  parse last JSON line     │
    │                      │  → payload               │
    │                      │  check _error            │
    │                      │  check max_rss_kb        │
    │                      │  → RunResult             │
    │◄─────────────────────│                          │
    │                                                 │
    │  _classify(RunResult)                           │
    │  _eq(result, expected)                          │
    │  → "Accepted" / "WrongAnswer" / "TLE" / ...     │
```

---

## 6. 安全设计

### 6.1 威胁模型与防护

| 威胁 | 攻击方式 | 防护措施 | 实现位置 |
|------|----------|----------|----------|
| 代码注入 | 用户代码 import os, 读写文件 | `-I` 隔离模式 + 最小 env + close_fds | executor.py |
| 内存炸弹 | 用户代码 `x = [0]*10**9` | `RLIMIT_AS` 256MB 硬限制 | executor.py harness |
| 死循环 | 用户代码 `while True: pass` | `proc.communicate(timeout=3.0)` → SIGKILL | executor.py |
| 信号劫持 | 用户代码 `signal.alarm(0)` 绕过超时 | `signal.signal(SIGALRM, SIG_IGN)` 屏蔽 | executor.py harness |
| 路径遍历 | 用户代码 `open("/etc/passwd")` | `-I` 隔离 + `PATH=/usr/bin:/bin` 最小环境 | executor.py |
| 子进程逃逸 | 用户代码 `os.fork()` / `subprocess.Popen()` | `RLIMIT_AS` 限制总内存 + 超时兜底 | executor.py |
| 密码泄露 | 数据库被拖 | SHA-256+salt 哈希存储 | auth.py |
| 时序攻击 | 密码哈希比较时间差 | `secrets.compare_digest` 常量时间比较 | auth.py |
| JWT 伪造 | 猜测密钥 | HS256 对称签名，密钥从环境变量注入 | auth.py |
| 隐藏测试泄露 | 请求 /api/problems/:id 试图获取 hidden_tests | `visible_problem_view()` 过滤，API 只返回 test_cases | problems.py / app.py |
| CORS 攻击 | 跨域请求伪造 | CORSMiddleware + allow_credentials | app.py |
| SQL 注入 | 构造恶意查询参数 | SQLAlchemy ORM 参数化查询 | db.py |

### 6.2 沙箱限制边界

```
┌──────────────────────────────────────────────────┐
│              沙箱安全边界                         │
├──────────────────────────────────────────────────┤
│                                                  │
│  ✓ 允许:                                        │
│    - 纯 Python 计算 (list/dict/str/int/float)    │
│    - 标准库 import (math, collections, itertools) │
│    - 定义函数和类                               │
│    - 递归 (受内存限制约束)                       │
│                                                  │
│  ✗ 限制:                                        │
│    - 内存 > 256MB → MemoryError                 │
│    - CPU > 3 秒 → SIGKILL                       │
│    - 文件系统访问 (路径限制在 env 内)             │
│    - 网络访问 (env 无网络相关变量)               │
│    - 子进程创建 (理论上可绕过，但受内存+超时约束)  │
│                                                  │
│  ⚠ 已知限制 (教学场景可接受):                    │
│    - 非 container 级隔离，root 用户可绕过 rlimit  │
│    - 无 seccomp 系统调用过滤                     │
│    - 无 namespace 隔离 (pid / mount / network)   │
│    - 生产环境应替换为 Docker / nsjail / firejail  │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## 7. 部署与运维

### 7.1 开发环境启动

#### 一键启动

```bash
./start.sh
```

`start.sh` 做的事情：
1. 检查 `app/.venv` 是否存在，不存在则创建并 `pip install -r requirements.txt`
2. 启动 `uvicorn app:app --host 127.0.0.1 --port 8001`
3. 检查 `web/node_modules` 是否存在，不存在则 `npm install`
4. 启动 `vite dev --port 5173 --host 127.0.0.1`
5. `wait -n` 等任一进程退出，然后 kill 两个进程

#### 分别启动

后端：
```bash
cd app
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8001 --log-level info
```

前端：
```bash
cd web
npm install
npm run dev
```

### 7.2 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CODING_JWT_SECRET` | `dev-secret-change-me` | JWT 签名密钥，**生产必须改** |
| `CODING_DB_PATH` | `app/data/coding.db` | SQLite 数据库文件路径 |
| `CODING_PROBLEMS_PATH` | `app/data/problems.json` | 题目数据文件路径 |
| `CODING_CORS_ORIGINS` | `*` | 逗号分隔的 CORS 白名单 |
| `EXEC_TIMEOUT_SEC` | `3.0` | 单条测试用例超时（秒） |
| `EXEC_MEM_MB` | `256` | 单条测试用例内存上限（MB） |
| `BACKEND_PORT` | `8001` | 后端端口（start.sh 用） |
| `FRONTEND_PORT` | `5173` | 前端端口（start.sh 用） |

### 7.3 前端代理配置

```typescript
// vite.config.ts
server: {
  proxy: {
    "/api": {
      target: "http://127.0.0.1:8001",
      changeOrigin: true,
    },
  },
}
```

开发模式下 Vite 将 `/api/*` 请求代理到后端 `:8001`，避免 CORS 问题。

### 7.4 生产部署建议

```
┌─────────────────────────────────────────────────────────────┐
│                    生产部署架构                              │
│                                                             │
│  ┌─────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Nginx     │─────►│  Uvicorn     │─────►│  SQLite   │ │
│  │  静态资源   │      │  (FastAPI)   │      │  coding.db│ │
│  │  反向代理   │      │  :8001       │      │           │ │
│  │  :80/:443   │      │  workers=4   │      │           │ │
│  └─────────────┘      └──────────────┘      └───────────┘ │
│        │                    │                              │
│        │                    │      ┌───────────────────┐   │
│        │                    └─────►│  subprocess 沙箱   │   │
│        │                           │  (python -I)      │   │
│  ┌─────┴─────┐                    │  RLIMIT_AS 256MB  │   │
│  │ web/dist  │                    │  timeout 3s       │   │
│  │ (npm build)│                    └───────────────────┘   │
│  └───────────┘                                             │
└─────────────────────────────────────────────────────────────┘
```

生产部署清单：
1. `npm run build` → `web/dist/` 静态资源
2. Nginx 配置：静态资源直接服务，`/api/*` 反向代理到 Uvicorn
3. `CODING_JWT_SECRET` 设置为强随机密钥
4. `CODING_CORS_ORIGINS` 设置为精确域名
5. Uvicorn `--workers N` 多进程（注意 SQLite 写锁瓶颈）
6. 定期备份 `coding.db`

---

## 8. 扩展规划

### 8.1 短期优化

| 优化项 | 方案 | 优先级 |
|--------|------|--------|
| 多语言支持 | executor 增加 C/C++/Java 编译执行路径 | 中 |
| 题目管理后台 | CRUD API + 管理界面，替代手动编辑 JSON | 中 |
| 排行榜 | 统计用户 AC 数 / 提交数 / 通过率 | 低 |
| 代码持久化 | localStorage / IndexedDB 自动保存草稿 | 低 |
| WebSocket 实时判分 | 替代轮询，长时任务进度推送 | 低 |

### 8.2 中期扩展

| 扩展项 | 方案 |
|--------|------|
| Docker 隔离沙箱 | 替换 subprocess + rlimit，使用 Docker container 执行用户代码 |
| PostgreSQL 迁移 | SQLAlchemy ORM 已抽象，切换 `create_engine` 连接串即可 |
| Redis 缓存 | 题目缓存 / 限流 / 排行榜 sorted set |
| 竞赛模式 | 定时开赛 + 实时排行榜 + 封榜 |
| 测试用例批量导入 | 支持 LeetCode 风格的 stdin/stdout 测试用例格式 |

### 8.3 架构演进路线

```
当前 (MVP)                    → 短期                    → 中期
─────────────────────────────────────────────────────────────────
SQLite + subprocess          → PostgreSQL + Docker     → PostgreSQL + Kubernetes
单进程 Uvicorn               → Nginx + Uvicorn×N       → Nginx + ASGI + Celery
静态 JSON 题库               → DB 题库 + 管理后台       → DB + Redis + CDN
JWT 无状态认证               → JWT + Refresh Token     → OAuth2 + RBAC
subprocess 沙箱              → Docker 沙箱             → gVisor / Kata Containers
```

---

## 附录

### A. 目录结构

```
coding_platform/
├── start.sh                    # 一键启动脚本
├── README.md                   # 项目说明
├── DESIGN.md                   # 本文档
├── app/                        # 后端 (FastAPI)
│   ├── app.py                  #   入口 + 路由 (167 行)
│   ├── auth.py                 #   认证模块 (50 行)
│   ├── db.py                   #   数据库 + ORM (54 行)
│   ├── models.py               #   Pydantic schema (70 行)
│   ├── executor.py             #   沙箱执行引擎 (87 行)
│   ├── judge.py                #   判分系统 (92 行)
│   ├── problems.py             #   题目加载器 (38 行)
│   ├── requirements.txt        #   Python 依赖
│   └── data/
│       ├── coding.db           #   SQLite 数据库 (自动创建)
│       ├── problems.json       #   题库数据
│       └── seed_problems.py    #   题目种子脚本
└── web/                        # 前端 (React + Vite + TS)
    ├── index.html
    ├── package.json
    ├── vite.config.ts          #   Vite 配置 + /api 代理
    ├── tsconfig.json
    └── src/
        ├── main.tsx            #   应用入口
        ├── App.tsx             #   路由 + Header
        ├── api.ts              #   HTTP client
        ├── types.ts            #   TypeScript 类型
        ├── styles.css          #   全局样式
        ├── context/
        │   └── AuthContext.tsx #   认证状态管理
        ├── components/
        │   ├── CodeEditor.tsx  #   CodeMirror 6 封装
        │   ├── TestPanel.tsx   #   测试结果展示
        │   └── SubmissionList.tsx
        └── pages/
            ├── Home.tsx        #   落地页
            ├── Login.tsx       #   登录
            ├── Register.tsx    #   注册
            ├── Problems.tsx    #   题目列表
            └── Editor.tsx      #   编辑器页
```

### B. 判分状态一览

| Status | 含义 | 触发条件 |
|--------|------|----------|
| Accepted | 全部测试通过 | 所有用例 `_eq(result, expected)` 为 True |
| WrongAnswer | 至少一条用例输出不匹配 | 执行成功但 `_eq` 返回 False |
| TLE | 至少一条用例超时 | `proc.communicate(timeout=3.0)` 超时 |
| MLE | 至少一条用例超内存 | `max_rss_kb > 256*1024*1.05` 或 MemoryError |
| RuntimeError | 用户代码抛异常 | IndexError / TypeError / ValueError 等 |
| CompileError | 用户代码无法定义 solve | 语法错误 / 缺少 solve 函数 |
| JudgeError | 判分系统出错 | harness 解析失败等异常 |

### C. 沙箱执行协议

**输入协议 (stdin → 子进程)：**

```json
{
  "params": [arg1, arg2, ...],   // 位置参数列表
  "kwargs": {}                    // 关键字参数（当前未使用）
}
```

**输出协议 (子进程 → stdout → 主进程)：**

成功时：
```json
{
  "result": <用户函数返回值>,
  "runtime_ms": 42,
  "max_rss_kb": 8192
}
```

失败时：
```json
{
  "_error": "compile: SyntaxError: invalid syntax",
  "runtime_ms": 1
}
```

**错误前缀分类：**

| 前缀 | 含义 | 映射状态 |
|------|------|----------|
| `compile:` | 用户代码执行阶段出错（定义 solve 前） | CompileError |
| `runtime:` | solve 函数调用阶段出错 | RuntimeError |
| `memory:` | Python 抛出 MemoryError | MLE |
| `serialize:` | 返回值无法 JSON 序列化 | JudgeError |
| `input_parse:` | stdin JSON 解析失败 | JudgeError |
