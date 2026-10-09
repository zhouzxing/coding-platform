import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api";

interface AuthState {
  user: { user_id: number; username: string; email: string | null } | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, email?: string) => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthState["user"]>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const tok = localStorage.getItem("token");
    if (!tok) { setLoading(false); return; }
    api.me()
      .then(setUser)
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setLoading(false));
  }, []);

  const save = (u: NonNullable<AuthState["user"]>, token: string) => {
    localStorage.setItem("token", token);
    localStorage.setItem("username", u.username);
    setUser(u);
  };

  const login = async (username: string, password: string) => {
    const r = await api.login({ username, password });
    save({ user_id: r.user_id, username: r.username, email: null }, r.access_token);
  };

  const register = async (username: string, password: string, email?: string) => {
    const r = await api.register({ username, password, email });
    save({ user_id: r.user_id, username: r.username, email: null }, r.access_token);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    setUser(null);
  };

  return <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}
