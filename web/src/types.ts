export interface Problem {
  id: number;
  title: string;
  difficulty: string;
  accept_rate: number | null;
  tags: string[];
}

export interface TestCase {
  input: Record<string, unknown>;
  expected: unknown;
}

export interface ProblemDetail extends Problem {
  description: string;
  signature: string;
  test_cases: TestCase[];
}

export interface TestResult {
  index: number;
  input: unknown;
  expected: unknown;
  got: unknown;
  verdict: string;
  status: string;
  runtime_ms: number;
  memory_kb: number;
}

export interface SubmitResult {
  submission_id: number;
  status: string;
  verdict: string;
  passed: number;
  total: number;
  time_ms: number;
  memory_kb: number;
  detail: { results: TestResult[] };
}

export interface Submission {
  id: number;
  user_id: number;
  problem_id: number;
  language: string;
  code: string;
  status: string;
  verdict: string;
  passed: number;
  total: number;
  time_ms: number;
  memory_kb: number;
  detail: { results: TestResult[] };
  created_at: string;
}
