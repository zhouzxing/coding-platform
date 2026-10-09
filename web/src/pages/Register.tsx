import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const nav = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      await register(username, password, email || undefined);
      nav("/problems");
    } catch (ex: any) {
      setErr(ex.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Register</h1>
        <form className="auth-form" onSubmit={submit}>
          <label>Username</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus minLength={2} />
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={4} />
          <label>Email (optional)</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <button className="primary" type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Creating..." : "Create account"}
          </button>
          {err && <div className="auth-error">{err}</div>}
        </form>
      </div>
    </div>
  );
}
