import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Problem } from "../types";

const DIFFS = ["All", "Easy", "Medium", "Hard"];

function diffClass(d: string) {
  return d.toLowerCase() === "easy" ? "easy" : d.toLowerCase() === "medium" ? "medium" : "hard";
}

export default function Problems() {
  const [items, setItems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [difficulty, setDifficulty] = useState("All");
  const [q, setQ] = useState("");

  useEffect(() => {
    setLoading(true);
    api.problems({
      difficulty: difficulty === "All" ? undefined : difficulty,
      q: q || undefined,
    })
      .then(setItems)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [difficulty, q]);

  return (
    <div className="container">
      <h1>Problems</h1>
      <div className="searchbar">
        <input
          placeholder="Search title or tag..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <div className="filter-group">
          {DIFFS.map((d) => (
            <button
              key={d}
              className={`filter-btn ${d.toLowerCase()} ${difficulty === d ? "active" : ""}`}
              onClick={() => setDifficulty(d)}
            >
              {d}
            </button>
          ))}
        </div>
      </div>
      {err && <div className="error">{err}</div>}
      {loading ? (
        <div className="loading">Loading problems...</div>
      ) : (
        <table className="problem-table">
          <thead>
            <tr>
              <th style={{ width: 60 }}>#</th>
              <th>Title</th>
              <th style={{ width: 100 }}>Difficulty</th>
              <th style={{ width: 120 }}>Tags</th>
              <th style={{ width: 100 }}>Accept</th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.id}>
                <td className="stat">{p.id}</td>
                <td>
                  <Link to={`/problems/${p.id}`} className="problem-link">
                    {p.title}
                  </Link>
                </td>
                <td>
                  <span className={`badge ${diffClass(p.difficulty)}`}>{p.difficulty}</span>
                </td>
                <td>
                  {p.tags.map((t) => (
                    <span key={t} className="badge tag" style={{ marginRight: 4 }}>
                      {t}
                    </span>
                  ))}
                </td>
                <td className="stat">
                  {p.accept_rate != null ? `${p.accept_rate.toFixed(1)}%` : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
