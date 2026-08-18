"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authApi, clearTokens, getCachedUser, getTokens, setCachedUser } from "./api";

/** Rol bo'yicha bosh sahifa — login/register muvaffaqiyatli bo'lganda shu yerga yo'naltiriladi. */
export function homeRouteFor(user) {
  if (!user) return "/login";
  if (user.is_pending_approval) return "/pending";
  const roles = user.roles || [];
  if (roles.includes("manager")) return "/manager";
  if (roles.includes("mentor")) return "/mentor";
  return "/dashboard";
}

export function hasRole(user, role) {
  return Boolean(user?.roles?.includes(role));
}

export function initials(user) {
  if (!user) return "?";
  const first = (user.first_name || "").trim();
  const last = (user.last_name || "").trim();
  if (first || last) return `${first[0] || ""}${last[0] || ""}`;
  return (user.username || "?").slice(0, 2);
}

export async function logout(router) {
  const { refresh } = getTokens();
  try {
    if (refresh) await authApi.logout(refresh);
  } catch {
    // Server sessiyani bekor qila olmasa ham lokal tokenlarni tozalaymiz
  }
  clearTokens();
  router.replace("/login");
}

/**
 * Joriy foydalanuvchini yuklaydi va sahifani himoya qiladi.
 *
 * @param {object} options
 * @param {string[]} options.roles      Ruxsat etilgan rollar (bo'sh = har qanday tizimga kirgan)
 * @param {boolean}  options.allowPending  Tasdiq kutayotgan o'quvchiga ruxsat berilsinmi
 */
export function useAuth({ roles = [], allowPending = false } = {}) {
  const router = useRouter();
  const [user, setUser] = useState(getCachedUser);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const { access } = getTokens();
      if (!access) {
        router.replace("/login");
        return;
      }
      try {
        const { data } = await authApi.me();
        if (cancelled) return;
        setCachedUser(data);
        setUser(data);

        if (data.is_pending_approval && !allowPending) {
          router.replace("/pending");
          return;
        }
        if (roles.length && !roles.some((r) => data.roles?.includes(r))) {
          router.replace(homeRouteFor(data));
          return;
        }
        setLoading(false);
      } catch {
        if (cancelled) return;
        clearTokens();
        router.replace("/login");
      }
    }

    load();
    return () => {
      cancelled = true;
    };
    // roles massivi har renderda yangi bo'lmasligi uchun stringga aylantiramiz
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, roles.join(","), allowPending]);

  return { user, loading };
}
