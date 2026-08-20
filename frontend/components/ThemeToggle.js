"use client";

import { useEffect, useRef, useState } from "react";
import { Moon, Sun } from "./Icons";
import { meApi } from "../lib/api";

const THEME_KEY = "edu_theme";

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem(THEME_KEY, theme);
}

function currentTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/**
 * Tun/kun rejimini almashtiruvchi tugma — barcha rollar uchun sarlavhada ko'rinadi.
 * Tanlov localStorage'da darhol qo'llanadi (yonib-o'chishni oldini olish uchun)
 * va profil sozlamalariga (`user.theme`) fon rejimida saqlanadi.
 */
export default function ThemeToggle({ user }) {
  const [theme, setTheme] = useState(null);
  const syncedFor = useRef(null);

  useEffect(() => {
    setTheme(currentTheme());
  }, []);

  // Profildan kelgan saqlangan tanlovni (masalan boshqa qurilmada o'zgartirilgan) qo'llash
  useEffect(() => {
    if (!user?.theme || syncedFor.current === user.id) return;
    syncedFor.current = user.id;
    if (!localStorage.getItem(THEME_KEY)) {
      applyTheme(user.theme);
      setTheme(user.theme);
    }
  }, [user]);

  function toggle() {
    const next = (theme || currentTheme()) === "dark" ? "light" : "dark";
    applyTheme(next);
    setTheme(next);
    if (user) {
      meApi.updateSettings({ theme: next }).catch(() => {});
    }
  }

  return (
    <button
      type="button"
      className="btn btn-ghost btn-sm theme-toggle"
      onClick={toggle}
      aria-label="Tun/kun rejimini almashtirish"
      title="Tun/kun rejimini almashtirish"
    >
      <Sun width={17} height={17} className="icon-sun" />
      <Moon width={17} height={17} className="icon-moon" />
    </button>
  );
}
