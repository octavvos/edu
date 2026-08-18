"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { authApi, clearTokens, getTokens, setCachedUser } from "../lib/api";
import { homeRouteFor } from "../lib/auth";

/**
 * Kirish nuqtasi: tizimga kirmagan foydalanuvchi login sahifasiga,
 * kirgan foydalanuvchi esa o'z roliga mos panelga yo'naltiriladi.
 */
export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    const { access } = getTokens();
    if (!access) {
      router.replace("/login");
      return;
    }
    authApi
      .me()
      .then(({ data }) => {
        setCachedUser(data);
        router.replace(homeRouteFor(data));
      })
      .catch(() => {
        clearTokens();
        router.replace("/login");
      });
  }, [router]);

  return (
    <div className="auth-page">
      <div className="row" style={{ gap: 10 }}>
        <span className="spinner" style={{ color: "var(--primary)" }} />
        <span className="muted">Yuklanmoqda…</span>
      </div>
    </div>
  );
}
