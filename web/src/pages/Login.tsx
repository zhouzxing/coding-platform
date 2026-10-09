import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const nav = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      await login(username, password);
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
        <h1>Login</h1>
        <form className="auth-form" onSubmit={submit}>
          <label>Username</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <button className="primary" type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Logging in..." : "Login"}
          </button>
          {err && <div className="auth-error">{err}</div>}
        </form>
      </div>
    </div>
  );
}
