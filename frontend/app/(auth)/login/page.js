"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import PasswordInput from "../../../components/PasswordInput";
import { authApi, errorMessage, setCachedUser, setTokens } from "../../../lib/api";
import { homeRouteFor } from "../../../lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await authApi.login(username.trim(), password);
      setTokens(data);
      setCachedUser(data.user);
      router.replace(homeRouteFor(data.user));
    } catch (err) {
      setError(errorMessage(err, "Username yoki parol noto'g'ri"));
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card fade-in">
        <div className="auth-head">
          <div className="logo-mark">E</div>
          <h1>Xush kelibsiz</h1>
          <p>Davom etish uchun hisobingizga kiring</p>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="username"
              autoComplete="username"
              autoFocus
              required
            />
          </div>

          <div className="field">
            <label htmlFor="password">Parol</label>
            <PasswordInput id="password" value={password} onChange={setPassword} />
          </div>

          <button className="btn btn-lg btn-block" type="submit" disabled={loading}>
            {loading && <span className="spinner" />}
            {loading ? "Kirilmoqda…" : "Kirish"}
          </button>
        </form>

        <div className="auth-foot">
          Hisobingiz yo&apos;qmi? <Link href="/register">Ro&apos;yxatdan o&apos;ting</Link>
        </div>
      </div>
    </div>
  );
}
