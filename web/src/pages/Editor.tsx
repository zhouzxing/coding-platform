import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import type { ProblemDetail, SubmitResult } from "../types";
import CodeEditor from "../components/CodeEditor";
import TestPanel from "../components/TestPanel";
import SubmissionList from "../components/SubmissionList";

export default function Editor() {
  const { id } = useParams();
  const pid = Number(id);
  const { user } = useAuth();
  const [prob, setProb] = useState<ProblemDetail | null>(null);
  const [err, setErr] = useState("");
  const [code, setCode] = useState("");
  const [visible, setVisible] = useState<SubmitResult | null>(null);
  const [hidden, setHidden] = useState<SubmitResult | null>(null);
  const [busy, setBusy] = useState<"" | "visible" | "submit">("");

  useEffect(() => {
    if (!pid) return;
    api.problem(pid)
      .then((p) => {
        setProb(p);
        setCode(p.signature + "\n    pass\n");
      })
      .catch((e) => setErr(e.message));
  }, [pid]);

  const runVisible = async () => {
    if (!prob) return;
    setBusy("visible");
    setVisible(null);
    try {
      setVisible(await api.runVisible(prob.id, code));
    } catch (e: any) {
      setVisible({ submission_id: 0, status: "JudgeError", verdict: e.message, passed: 0, total: 0, time_ms: 0, memory_kb: 0, detail: { results: [] } });
    } finally {
      setBusy("");
    }
  };

  const submit = async () => {
    if (!prob) return;
    if (!user) { alert("请先登录再提交"); return; }
    setBusy("submit");
    setHidden(null);
    try {
      setHidden(await api.run(prob.id, code));
    } catch (e: any) {
      setHidden({ submission_id: 0, status: "JudgeError", verdict: e.message, passed: 0, total: 0, time_ms: 0, memory_kb: 0, detail: { results: [] } });
    } finally {
      setBusy("");
    }
  };

  if (err) return <div className="container"><div className="error">{err}</div></div>;
  if (!prob) return <div className="container"><div className="loading">Loading problem...</div></div>;

  return (
    <div className="container" style={{ padding: "16px 24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <Link to="/problems" style={{ color: "#7d8590" }}>← Back</Link>
        <h2 style={{ margin: 0 }}>{prob.id}. {prob.title}</h2>
        <span className={`badge ${prob.difficulty.toLowerCase()}`}>{prob.difficulty}</span>
        <span className="stat">{prob.accept_rate != null ? `${prob.accept_rate.toFixed(1)}% accepted` : ""}</span>
        <span style={{ flex: 1 }} />
        <button onClick={runVisible} disabled={busy !== ""}>
          {busy === "visible" ? "Running..." : "▶ Run Visible"}
        </button>
        <button className="primary" onClick={submit} disabled={busy !== ""}>
          {busy === "submit" ? "Submitting..." : "✓ Submit"}
        </button>
      </div>

      <div className="editor-layout">
        <div className="panel">
          <div className="panel-header">Problem</div>
          <div className="panel-body md">
            <ReactMarkdown>{prob.description}</ReactMarkdown>
            {prob.tags.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <strong>Tags:</strong> {prob.tags.map((t) => (
                  <span key={t} className="badge tag" style={{ marginLeft: 4 }}>{t}</span>
                ))}
              </div>
            )}
            {visible && (
              <div style={{ marginTop: 12 }}>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Visible Tests</div>
                <TestPanel result={visible} title="Result" />
              </div>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <span>Python Editor</span>
            <button onClick={() => setCode(prob.signature + "\n    pass\n")} style={{ padding: "2px 8px", fontSize: 12 }}>Reset</button>
          </div>
          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <div style={{ flex: 1, minHeight: 300, overflow: "hidden" }}>
              <CodeEditor value={code} onChange={setCode} readOnly={false} />
            </div>
            {hidden && (
              <div style={{ maxHeight: 320, overflow: "auto", borderTop: "1px solid #30363d" }}>
                <TestPanel result={hidden} title="Hidden Tests" />
              </div>
            )}
          </div>
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>My Submissions</h3>
        <SubmissionList problemId={prob.id} />
      </div>
    </div>
  );
}
