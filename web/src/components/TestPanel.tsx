import React from "react";
import type { SubmitResult } from "../types";

export default function TestPanel({ result, title }: { result: SubmitResult | null; title: string }) {
  if (!result) {
    return (
      <div>
        <div className="panel-header">{title}</div>
        <div className="panel-body">
          <div className="empty">尚未运行。点击 Run 或 Submit 开始。</div>
        </div>
      </div>
    );
  }
  const statusClass = result.status.toLowerCase();
  return (
    <div>
      <div className="panel-header">
        <span>{title}</span>
        <span className={`pill ${result.status}`}>{result.status}</span>
      </div>
      <div className="panel-body">
        <div className="stat-row">
          <span><strong>{result.passed}</strong> / {result.total} passed</span>
          <span>Time: <strong>{result.time_ms} ms</strong></span>
          <span>Mem: <strong>{(result.memory_kb / 1024).toFixed(1)} MB</strong></span>
        </div>
        <div style={{ marginBottom: 8, color: "#7d8590", fontSize: 13 }}>{result.verdict}</div>
        {result.detail.results.map((r) => {
          const cls =
            r.status === "Accepted" ? "accepted" :
            r.status === "WrongAnswer" ? "wrong" :
            r.status === "TLE" || r.status === "MLE" ? "tle" :
            r.status === "RuntimeError" ? "runtime" : "compile";
          return (
            <div key={r.index} className={`result-card ${cls}`}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <strong>Test #{r.index + 1}</strong>
                <span className={`pill ${r.status}`}>{r.status}</span>
              </div>
              <div style={{ fontSize: 12, color: "#7d8590", marginBottom: 4 }}>
                input: <code>{JSON.stringify(r.input)}</code>
              </div>
              {r.status === "Accepted" || r.status === "OK" ? (
                <div style={{ fontSize: 13 }}>✓ Passed</div>
              ) : (
                <>
                  <div style={{ fontSize: 13, marginBottom: 2 }}>
                    expected: <code style={{ color: "#3fb950" }}>{JSON.stringify(r.expected)}</code>
                  </div>
                  {r.got !== null && r.got !== undefined && (
                    <div style={{ fontSize: 13, marginBottom: 4 }}>
                      got: <code style={{ color: "#f85149" }}>{JSON.stringify(r.got)}</code>
                    </div>
                  )}
                  <div style={{ fontSize: 12, color: "#7d8590" }}>{r.verdict}</div>
                </>
              )}
              <div style={{ fontSize: 11, color: "#7d8590", marginTop: 4 }}>
                {r.runtime_ms} ms / {(r.memory_kb / 1024).toFixed(1)} MB
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
