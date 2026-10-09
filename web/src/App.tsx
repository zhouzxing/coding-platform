import React from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Problems from "./pages/Problems";
import Editor from "./pages/Editor";

function Header() {
  const { user, loading, logout } = useAuth();
  const loc = useLocation();
  return (
    <header className="header">
      <div className="logo">
        <Link to="/">Coding<span className="accent">Platform</span></Link>
      </div>
      <nav className="nav">
        <Link to="/" className={loc.pathname === "/" ? "active" : ""}>Home</Link>
        <Link to="/problems" className={loc.pathname.startsWith("/problems") ? "active" : ""}>Problems</Link>
      </nav>
      <div className="user-area">
        {loading ? (
          <span style={{ color: "#7d8590" }}>...</span>
        ) : user ? (
          <>
            <span style={{ color: "#7d8590" }}>👤 {user.username}</span>
            <button onClick={logout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" style={{ color: "#e6edf3" }}>Login</Link>
            <Link to="/register"><button className="primary">Register</button></Link>
          </>
        )}
      </div>
    </header>
  );
}

export default function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/problems" element={<Problems />} />
        <Route path="/problems/:id" element={<Editor />} />
      </Routes>
    </>
  );
}
