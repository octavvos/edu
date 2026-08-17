"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi, setTokens } from "../../../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await authApi.login(identifier, password);
      setTokens(data);
      router.push("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Kirishda xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section style={{ maxWidth: 380, margin: "0 auto" }}>
      <h1>Kirish</h1>
      <form onSubmit={handleSubmit}>
        <input
          placeholder="Telefon yoki email"
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Parol"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <button className="btn" type="submit" disabled={loading}>
          {loading ? "Kirilmoqda..." : "Kirish"}
        </button>
      </form>
      <p>
        Hisobingiz yo&apos;qmi? <a href="/otp">Telefon orqali kirish</a> yoki{" "}
        <a href="/register">ro&apos;yxatdan o&apos;ting</a>.
      </p>
    </section>
  );
}
