# Coding Platform

在线编程练习平台。0-1 从零构建，像 LeetCode 一样刷题。

## 功能
- **注册 / 登录**：JWT 认证，SHA-256+salt 密码哈希
- **题目列表**：6 道经典题（Two Sum / Valid Anagram / Max Subarray / Two Sum II / Reverse Linked List / Binary Search），难度筛选 + 关键词搜索
- **题目详情**：Markdown 题面渲染 + CodeMirror 6 代码编辑器 + 可见测试 + 隐藏测试
- **实时判分**：`Run` 跑可见测试，`Submit` 跑完整隐藏测试集，秒级反馈
- **提交记录**：保存每次提交的代码 / 状态 / 通过率 / 耗时 / 内存
- **沙箱执行**：subprocess + `resource.setrlimit` 隔离执行，超时 / 内存限制 / 异常捕获全兜底

## 技术栈
| 层 | 技术 |
|---|---|
| 后端 | Python 3.11+ · FastAPI · SQLAlchemy · SQLite · PyJWT |
| 沙箱 | `subprocess.Popen` + `resource.setrlimit(RLIMIT_AS)` + `-I` 隔离 Python |
| 前端 | React 18 + TypeScript + Vite |
| 编辑器 | CodeMirror 6（`@codemirror/lang-python` + oneDark 主题） |
| Markdown | react-markdown |

## 快速启动

### 一键
```bash
./start.sh
```
打开 `http://127.0.0.1:5173`。

### 分别启动

后端（`:8001`）：
```bash
cd app
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8001 --log-level info
```

前端（`:5173`，Vite 自动代理 `/api` → `:8001`）：
```bash
cd web
npm install
npm run dev
```

## 环境变量
| 变量 | 默认 | 说明 |
|---|---|---|
| `CODING_JWT_SECRET` | `dev-secret-change-me` | JWT 签名密钥，生产必须改 |
| `CODING_DB_PATH` | `app/data/coding.db` | SQLite 数据库路径 |
| `CODING_PROBLEMS_PATH` | `app/data/problems.json` | 题目数据文件 |
| `CODING_CORS_ORIGINS` | `*` | 逗号分隔的 CORS 白名单 |
| `EXEC_TIMEOUT_SEC` | `3.0` | 单条测试用例超时（秒） |
| `EXEC_MEM_MB` | `256` | 单条测试用例内存上限（MB） |

## 目录结构
```
coding_platform/
├── start.sh                    # 一键启动
├── README.md
├── app/                        # 后端 (FastAPI)
│   ├── app.py                  # FastAPI 入口 + 路由
│   ├── auth.py                 # JWT + 密码哈希
│   ├── db.py                   # SQLAlchemy + SQLite
│   ├── models.py               # Pydantic schemas
│   ├── executor.py             # 沙箱执行引擎
│   ├── judge.py                # 测试用例判分
│   ├── problems.py             # 题目加载器
│   ├── requirements.txt
│   └── data/
│       ├── coding.db           # SQLite (自动生成)
│       ├── problems.json       # 6 道题 (自动生成)
│       └── seed_problems.py    # 题目种子脚本
└── web/                        # 前端 (React + Vite + TS)
    ├── index.html
    ├── package.json
    ├── vite.config.ts          # /api 代理到 :8001
    ├── tsconfig.json
    └── src/
        ├── main.tsx
        ├── App.tsx             # 路由 + Header
        ├── api.ts              # fetch client
        ├── types.ts
        ├── styles.css
        ├── context/AuthContext.tsx
        ├── components/
        │   ├── CodeEditor.tsx  # CodeMirror 6 wrapper
        │   ├── TestPanel.tsx   # 测试结果展示
        │   └── SubmissionList.tsx
        └── pages/
            ├── Home.tsx
            ├── Login.tsx
            ├── Register.tsx
            ├── Problems.tsx
            └── Editor.tsx
```

## API 端点
| Method | Path | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| POST | `/api/auth/register` | 注册，返回 JWT |
| POST | `/api/auth/login` | 登录，返回 JWT |
| GET | `/api/auth/me` | 当前用户信息（需 JWT） |
| GET | `/api/problems?difficulty=&q=` | 题目列表（可筛选） |
| GET | `/api/problems/{id}` | 题目详情（含可见测试，不含隐藏） |
| POST | `/api/problems/{id}/run/visible` | 跑可见测试（可匿名） |
| POST | `/api/problems/{id}/run` | 跑隐藏测试 + 保存记录（需 JWT） |
| GET | `/api/submissions` | 当前用户的提交记录 |

## 沙箱执行原理
用户代码在独立子进程中执行，主进程只做超时和内存监控：
1. **进程隔离**：`subprocess.Popen([python -I, -c, harness])` + `close_fds=True` + 最小 `env`
2. **内存限制**：harness 内 `resource.setrlimit(RLIMIT_AS, 256MB)`，超限内核直接 OOM
3. **CPU 超时**：父进程 `proc.communicate(timeout=3.0)`，超时 `SIGKILL` 子进程
4. **信号屏蔽**：harness 里 `signal.signal(SIGALRM, SIG_IGN)`，防止用户代码劫持
5. **协议**：stdin 传 `{params, kwargs}` JSON，stdout 传 `{result, runtime_ms, max_rss_kb}` JSON

`_wrap_input` 把题目 `input: {a: x, b: y}` 转成 `solve(a=x, b=y)` 位置参数列表，与题面 `signature` 声明一致。

## 判分状态
| Status | 含义 |
|---|---|
| Accepted | 全部测试通过 |
| WrongAnswer | 至少一条测试用例输出不匹配 |
| TLE | 至少一条用例超过 3 秒 |
| MLE | 至少一条用例超过 256MB 内存，或 Python 抛 `MemoryError` |
| RuntimeError | 用户代码抛异常（包括 MemoryError、IndexError 等） |
| CompileError | 用户代码无法定义 `solve` 函数 |
| JudgeError | 判分系统本身出错 |

## 添加新题目
编辑 `app/data/problems.json`（或直接改 `seed_problems.py` 后重跑）：
```json
{
  "id": 7,
  "title": "New Problem",
  "difficulty": "Easy",
  "accept_rate": 0,
  "tags": ["Array"],
  "description": "## 题目\n\nMarkdown 题面...",
  "signature": "def solve(nums: list[int]) -> int:",
  "test_cases": [{"input": {"nums": [1,2,3]}, "expected": 6}],
  "hidden_tests": [{"input": {"nums": [4,5,6]}, "expected": 15}]
}
```
`signature` 里的函数名必须是 `solve`，参数与 `test_cases[].input` 的 key 一致。
