"use client";

import { createContext, useCallback, useContext, useRef, useState } from "react";
import { X } from "./Icons";

const NotificationContext = createContext(null);

const TOAST_TTL_MS = 5000;
const MAX_HISTORY = 50;

let seq = 0;
function nextId() {
  seq += 1;
  return `n${Date.now()}-${seq}`;
}

/**
 * Root layout'ga o'ralgan — shuning uchun sahifalar orasida almashganda ham
 * bildirishnoma tarixi va hozir ko'rinayotgan qalqib chiquvchilar saqlanib qoladi.
 * `notify({ type, text })` — mavjud `setMessage({ type, text })` chaqiruvlari
 * bilan bir xil shaklda, shuning uchun sahifalarda faqat nom almashtiriladi.
 */
export function NotificationProvider({ children }) {
  const [items, setItems] = useState([]); // to'liq tarix — yangisi tepada
  const [toasts, setToasts] = useState([]); // hozir qalqib turgan bildirishnomalar
  const [unreadCount, setUnreadCount] = useState(0);
  const timers = useRef({});

  const notify = useCallback((payload) => {
    const text = typeof payload === "string" ? payload : payload?.text;
    if (!text) return undefined;
    const type = (typeof payload === "object" && payload?.type) || "info";
    const item = { id: nextId(), type, text, createdAt: Date.now() };

    setItems((prev) => [item, ...prev].slice(0, MAX_HISTORY));
    setUnreadCount((prev) => prev + 1);
    setToasts((prev) => [...prev, item]);

    timers.current[item.id] = setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== item.id));
      delete timers.current[item.id];
    }, TOAST_TTL_MS);

    return item.id;
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    if (timers.current[id]) {
      clearTimeout(timers.current[id]);
      delete timers.current[id];
    }
  }, []);

  const markAllRead = useCallback(() => setUnreadCount(0), []);

  return (
    <NotificationContext.Provider value={{ items, unreadCount, notify, markAllRead }}>
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
