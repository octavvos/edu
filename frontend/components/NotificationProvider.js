"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { X } from "./Icons";
import { getTokens, notificationsApi } from "../lib/api";

const NotificationContext = createContext(null);

const TOAST_TTL_MS = 5000;
const MAX_HISTORY = 50;
const MAX_READ_IDS = 200;
const POLL_INTERVAL_MS = 15000;
const LAST_READ_KEY = "edu_notif_last_read_at";
const READ_IDS_KEY = "edu_notif_read_ids";

let seq = 0;
function nextId() {
  seq += 1;
  return `n${Date.now()}-${seq}`;
}

function getLastReadAt() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(LAST_READ_KEY);
}

function setLastReadAt(iso) {
  if (typeof window === "undefined") return;
  localStorage.setItem(LAST_READ_KEY, iso);
}

/** Alohida o'qilgan deb belgilangan bildirishnomalar — reload'dan keyin ham nuqtasi qaytmasin. */
function getReadIds() {
  if (typeof window === "undefined") return new Set();
  try {
    return new Set(JSON.parse(localStorage.getItem(READ_IDS_KEY) || "[]"));
  } catch {
    return new Set();
  }
}

function addReadId(id) {
  if (typeof window === "undefined") return;
  const ids = [...getReadIds(), id].slice(-MAX_READ_IDS);
  localStorage.setItem(READ_IDS_KEY, JSON.stringify(ids));
}

/**
 * Root layout'ga o'ralgan — shuning uchun sahifalar orasida almashganda ham
 * bildirishnoma tarixi va hozir ko'rinayotgan qalqib chiquvchilar saqlanib qoladi.
 * `notify({ type, text })` — mavjud `setMessage({ type, text })` chaqiruvlari
 * bilan bir xil shaklda, shuning uchun sahifalarda faqat nom almashtiriladi.
 *
 * Bundan tashqari `/api/v1/notifications/mine/` ni davriy so'raydi (polling) —
 * masalan mentor guruhga vazifa jo'natganda, o'quvchi hali sahifani ochmagan
 * bo'lsa ham, keyingi so'rovda bu haqidagi bildirishnoma toast+qo'ng'iroqchada
 * paydo bo'ladi.
 */
export function NotificationProvider({ children }) {
  const [items, setItems] = useState([]); // to'liq tarix — yangisi tepada
  const [toasts, setToasts] = useState([]); // hozir qalqib turgan bildirishnomalar
  const [unreadCount, setUnreadCount] = useState(0);
  const timers = useRef({});

  const pushItem = useCallback((item) => {
    setItems((prev) => [{ ...item, read: false }, ...prev].slice(0, MAX_HISTORY));
    setUnreadCount((prev) => prev + 1);
    setToasts((prev) => [...prev, item]);

    timers.current[item.id] = setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== item.id));
      delete timers.current[item.id];
    }, TOAST_TTL_MS);
  }, []);

  const notify = useCallback((payload) => {
    const text = typeof payload === "string" ? payload : payload?.text;
    if (!text) return undefined;
    const type = (typeof payload === "object" && payload?.type) || "info";
    const id = nextId();
    pushItem({ id, type, text, createdAt: Date.now() });
    return id;
  }, [pushItem]);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    if (timers.current[id]) {
      clearTimeout(timers.current[id]);
      delete timers.current[id];
    }
  }, []);

  const markAllRead = useCallback(() => {
    setUnreadCount(0);
    setLastReadAt(new Date().toISOString());
  }, []);

  /** Bitta bildirishnoma bosilganda — oldidagi nuqta yo'qoladi, reload'dan keyin ham qaytmaydi. */
  const markItemRead = useCallback((id) => {
    setItems((prev) => prev.map((it) => (it.id === id ? { ...it, read: true } : it)));
    addReadId(id);
  }, []);

  // Serverdagi bildirishnomalarni davriy so'rash — boshqa foydalanuvchi
  // (masalan mentor) qilgan amal haqida xabar berish uchun.
  useEffect(() => {
    let cancelled = false;
    let seeded = false;
    let sinceIso = null;

    async function poll() {
      const { access } = getTokens();
      if (!access) return;
      try {
        const { data } = await notificationsApi.mine(seeded ? sinceIso : undefined);
        if (cancelled || !data?.length) return;

        if (!seeded) {
          const lastReadAt = getLastReadAt() || new Date().toISOString();
          if (!getLastReadAt()) setLastReadAt(lastReadAt);
          const readIds = getReadIds();
          const fresh = data.map((r) => ({
            id: r.id, type: r.type, text: r.text, event: r.event,
            createdAt: new Date(r.created_at).getTime(), read: readIds.has(r.id),
          }));
          const unread = data.filter((r) => r.created_at > lastReadAt).length;
          setItems((prev) => [...fresh].reverse().concat(prev).slice(0, MAX_HISTORY));
          if (unread > 0) setUnreadCount((prev) => prev + unread);
        } else {
          data.forEach((r) => {
            pushItem({
              id: r.id, type: r.type, text: r.text, event: r.event,
              createdAt: new Date(r.created_at).getTime(),
            });
          });
        }

        sinceIso = data[data.length - 1].created_at;
        seeded = true;
      } catch {
        // jim — keyingi urinishda qayta so'raladi
      }
    }

    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <NotificationContext.Provider value={{ items, unreadCount, notify, markAllRead, markItemRead }}>
      {children}
      <ToastStack toasts={toasts} onDismiss={dismissToast} />
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications faqat NotificationProvider ichida ishlatiladi");
  return ctx;
}

/** Ko'pchilik sahifalarga shu kifoya — {type, text} bilan chaqiriladi. */
export function useNotify() {
  return useNotifications().notify;
}

// ---------------------------------------------------------------------------

function ToastStack({ toasts, onDismiss }) {
  if (toasts.length === 0) return null;
  return (
    <div className="toast-stack" role="status" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          <span className="toast-text">{t.text}</span>
          <button
            type="button"
            className="toast-close"
            onClick={() => onDismiss(t.id)}
            aria-label="Yopish"
          >
            <X width={13} height={13} />
          </button>
        </div>
      ))}
    </div>
  );
}
