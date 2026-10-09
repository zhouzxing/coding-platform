import React, { useEffect, useState } from "react";
import { api } from "../api";
import type { Submission } from "../types";

export default function SubmissionList({ problemId }: { problemId?: number }) {
  const [items, setItems] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.submissions(problemId)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [problemId]);

  if (loading) return <div className="loading">Loading submissions...</div>;
  if (items.length === 0) return <div className="empty">No submissions yet.</div>;

  return (
    <div>
      <div className="sub-row head">
        <span>#</span>
        <span>Status</span>
        <span>Passed</span>
        <span>Time</span>
        <span>When</span>
      </div>
      {items.map((s) => (
        <div key={s.id} className="sub-row">
          <span className="stat">{s.id}</span>
          <span>
            <span className={`pill ${s.status}`}>{s.status}</span>
          </span>
          <span>{s.passed}/{s.total}</span>
          <span className="stat">{s.time_ms} ms</span>
          <span className="stat">{new Date(s.created_at).toLocaleString()}</span>
        </div>
      ))}
    </div>
  );
}
