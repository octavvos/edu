"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi, setTokens } from "../../../lib/api";

function getOrCreateDeviceId() {
  if (typeof window === "undefined") return "";
  let id = localStorage.getItem("device_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("device_id", id);
  }
  return id;
}

export default function OtpLoginPage() {
  const router = useRouter();
  const [step, setStep] = useState("phone"); // "phone" | "code"
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendOtp(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.sendOtp(phone);
      setStep("code");
    } catch (err) {
      setError(err.response?.data?.detail || "SMS yuborishda xatolik");
    } finally {
      setLoading(false);
    }
  }

  async function verifyOtp(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await authApi.verifyOtp(phone, code, getOrCreateDeviceId());
      setTokens(data);
      router.push("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Kod noto'g'ri");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section style={{ maxWidth: 380, margin: "0 auto" }}>
      <h1>Telefon orqali kirish</h1>
      {step === "phone" ? (
        <form onSubmit={sendOtp}>
          <input
            placeholder="+998901234567" value={phone}
            onChange={(e) => setPhone(e.target.value)} required
          />
          {error && <p style={{ color: "crimson" }}>{error}</p>}
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Yuborilmoqda..." : "SMS kod olish"}
          </button>
        </form>
      ) : (
        <form onSubmit={verifyOtp}>
          <p>{phone} raqamiga yuborilgan 6 xonali kodni kiriting.</p>
          <input
            placeholder="000000" value={code} maxLength={6}
            onChange={(e) => setCode(e.target.value)} required
          />
          {error && <p style={{ color: "crimson" }}>{error}</p>}
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Tekshirilmoqda..." : "Tasdiqlash"}
          </button>
        </form>
      )}
    </section>
  );
}
