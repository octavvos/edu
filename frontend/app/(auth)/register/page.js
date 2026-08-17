"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "../../../lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.registerEmail(email, password, fullName);
      setDone(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Ro'yxatdan o'tishda xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <section style={{ maxWidth: 380, margin: "0 auto" }}>
        <h1>Emailingizni tekshiring</h1>
        <p>Tasdiqlash havolasi {email} manziliga yuborildi.</p>
        <a className="btn" href="/login">Kirish sahifasiga qaytish</a>
      </section>
    );
  }

  return (
    <section style={{ maxWidth: 380, margin: "0 auto" }}>
      <h1>Ro&apos;yxatdan o&apos;tish</h1>
      <form onSubmit={handleSubmit}>
        <input placeholder="F.I.Sh." value={fullName} onChange={(e) => setFullName(e.target.value)} />
        <input
          type="email" placeholder="Email" value={email}
          onChange={(e) => setEmail(e.target.value)} required
        />
        <input
          type="password" placeholder="Parol (kamida 8 belgi)" value={password}
          onChange={(e) => setPassword(e.target.value)} required minLength={8}
        />
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <button className="btn" type="submit" disabled={loading}>
          {loading ? "Yuborilmoqda..." : "Ro'yxatdan o'tish"}
        </button>
      </form>
      <p>
        Telefon orqali ro&apos;yxatdan o&apos;tishni afzal ko&apos;rasizmi?{" "}
        <a href="/otp">Bu yerga bosing</a>.
      </p>
    </section>
  );
}
