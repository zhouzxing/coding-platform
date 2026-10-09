import type { Problem, ProblemDetail, Submission, SubmitResult } from "./types";

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const r = await fetch(path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  if (!r.ok) {
    const body = await r.text();
    throw new Error(`${r.status}: ${body}`.slice(0, 300));
  }
  return r.json() as Promise<T>;
}

function authHeader(): Record<string, string> {
  const tok = localStorage.getItem("token");
  return tok ? { Authorization: `Bearer ${tok}` } : {};
}

export const api = {
  health: () => req<{ status: string }>("/api/health"),
  problems: (params?: { difficulty?: string; q?: string }) => {
    const usp = new URLSearchParams();
    if (params?.difficulty) usp.set("difficulty", params.difficulty);
    if (params?.q) usp.set("q", params.q);
    return req<Problem[]>(`/api/problems?${usp}`);
  },
  problem: (id: number) => req<ProblemDetail>(`/api/problems/${id}`),
  register: (body: { username: string; password: string; email?: string }) =>
    req<{ access_token: string; user_id: number; username: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  login: (body: { username: string; password: string }) =>
    req<{ access_token: string; user_id: number; username: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  me: () =>
    req<{ user_id: number; username: string; email: string | null }>("/api/auth/me", {
      headers: authHeader(),
    }),
  runVisible: (id: number, code: string) =>
    req<SubmitResult>(`/api/problems/${id}/run/visible`, {
      method: "POST",
      body: JSON.stringify({ problem_id: id, language: "python", code }),
    }),
  run: (id: number, code: string) =>
    req<SubmitResult>(`/api/problems/${id}/run`, {
      method: "POST",
      body: JSON.stringify({ problem_id: id, language: "python", code }),
      headers: authHeader(),
    }),
  submissions: (problemId?: number) => {
    const q = problemId ? `?problem_id=${problemId}` : "";
    return req<Submission[]>(`/api/submissions${q}`, { headers: authHeader() });
  },
};
