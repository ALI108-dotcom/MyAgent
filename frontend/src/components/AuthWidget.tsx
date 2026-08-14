"use client";

import { useEffect, useState } from "react";
import { User } from "@/types/auth";
import { clearAuthToken, fetchCurrentUser, getAuthToken, loginUser, registerUser } from "@/lib/api";

export function AuthWidget() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [tab, setTab] = useState<"login" | "register">("login");
  const [username, setUsername] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [role, setRole] = useState<"user" | "admin">("user");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const isDev = process.env.NODE_ENV === "development";

  useEffect(() => {
    loadUser();
  }, []);

  async function loadUser() {
    setLoading(true);
    const token = getAuthToken();
    if (!token) {
      setCurrentUser(null);
      setLoading(false);
      return;
    }
    try {
      const user = await fetchCurrentUser();
      setCurrentUser(user);
    } catch {
      clearAuthToken();
      setCurrentUser(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg(null);
    try {
      const res = await loginUser({ username, password });
      setCurrentUser(res.user);
      setIsModalOpen(false);
      setUsername("");
      setPassword("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Login failed";
      setErrorMsg(msg);
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg(null);
    try {
      await registerUser({ username, email, password, role });
      const res = await loginUser({ username, password });
      setCurrentUser(res.user);
      setIsModalOpen(false);
      setUsername("");
      setEmail("");
      setPassword("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Registration failed";
      setErrorMsg(msg);
    }
  }

  function handleLogout() {
    clearAuthToken();
    setCurrentUser(null);
  }

  function prefillAccount(uname: string, pass: string) {
    setUsername(uname);
    setPassword(pass);
  }

  return (
    <div className="relative">
      {loading ? (
        <div className="h-9 w-24 bg-slate-800 animate-pulse rounded-md" />
      ) : currentUser ? (
        <div className="flex items-center gap-3 bg-slate-800/80 border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-200 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-semibold text-slate-100">{currentUser.username}</span>
            <span
              className={`px-1.5 py-0.5 text-[10px] font-bold rounded uppercase ${
                currentUser.role === "admin"
                  ? "bg-purple-900/60 text-purple-300 border border-purple-700/50"
                  : "bg-blue-900/60 text-blue-300 border border-blue-700/50"
              }`}
            >
              {currentUser.role}
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="text-slate-400 hover:text-rose-400 transition-colors font-medium ml-1"
          >
            Logout
          </button>
        </div>
      ) : (
        <button
          onClick={() => {
            setErrorMsg(null);
            setIsModalOpen(true);
          }}
          className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-3.5 py-1.5 rounded-lg shadow-sm transition-colors"
        >
          Sign In
        </button>
      )}

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white text-lg font-bold"
            >
              ×
            </button>

            <div className="flex items-center gap-4 border-b border-slate-800 pb-3 mb-4">
              <button
                onClick={() => {
                  setTab("login");
                  setErrorMsg(null);
                }}
                className={`text-sm font-semibold pb-1 transition-colors ${
                  tab === "login"
                    ? "text-emerald-400 border-b-2 border-emerald-400"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Sign In
              </button>
              <button
                onClick={() => {
                  setTab("register");
                  setErrorMsg(null);
                }}
                className={`text-sm font-semibold pb-1 transition-colors ${
                  tab === "register"
                    ? "text-emerald-400 border-b-2 border-emerald-400"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Register
              </button>
            </div>

            {errorMsg && (
              <div className="bg-rose-950/80 border border-rose-800 text-rose-300 text-xs rounded-lg p-2.5 mb-4">
                {errorMsg}
              </div>
            )}

            {tab === "login" ? (
              <form onSubmit={handleLogin} className="space-y-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Username</label>
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                    placeholder="Enter username"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Password</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                    placeholder="Enter password"
                  />
                </div>

                {isDev && (
                  <div className="pt-2 flex items-center justify-between gap-2">
                    <span className="text-[11px] text-slate-500">Quick Test Credentials (Dev Only):</span>
                    <div className="flex gap-1.5">
                      <button
                        type="button"
                        onClick={() => prefillAccount("admin", "AdminPass123!")}
                        className="text-[10px] bg-purple-950 hover:bg-purple-900 border border-purple-800/80 text-purple-300 px-2 py-0.5 rounded"
                      >
                        Admin
                      </button>
                      <button
                        type="button"
                        onClick={() => prefillAccount("user", "UserPass123!")}
                        className="text-[10px] bg-blue-950 hover:bg-blue-900 border border-blue-800/80 text-blue-300 px-2 py-0.5 rounded"
                      >
                        User
                      </button>
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  className="w-full mt-4 bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2 rounded-lg text-sm transition-colors"
                >
                  Sign In
                </button>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="space-y-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Username</label>
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                    placeholder="Choose username"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Email</label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                    placeholder="email@agentai.dev"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Password</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                    placeholder="Choose password (min 8 chars, A-z, 0-9, special)"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Role</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value as "user" | "admin")}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="user">User (Standard)</option>
                    <option value="admin">Admin (Full System Permissions)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  className="w-full mt-4 bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2 rounded-lg text-sm transition-colors"
                >
                  Create Account
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
