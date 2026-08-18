"use client";

import { useEffect, useRef, useState } from "react";
import { Bell } from "./Icons";
import { useNotifications } from "./NotificationProvider";

/** Sarlavhadagi qo'ng'iroqcha — bosilganda tarix pastga ketma-ket ochiladi. */
export default function NotificationBell() {
  const { items, unreadCount, markAllRead } = useNotifications();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    function onClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  function toggle() {
    setOpen((v) => {
      if (!v) markAllRead();
      return !v;
    });
  }

  return (
    <div className="notif-bell" ref={ref}>
      <button
        type="button"
        className="btn btn-ghost btn-sm notif-bell-btn"
        onClick={toggle}
        aria-label="Bildirishnomalar"
        aria-expanded={open}
      >
        <Bell width={17} height={17} />
        {unreadCount > 0 && (
          <span className="notif-badge">{unreadCount > 9 ? "9+" : unreadCount}</span>
        )}
      </button>

      {open && (
        <div className="notif-dropdown fade-in">
          <div className="notif-dropdown-head">Bildirishnomalar</div>
          {items.length === 0 ? (
            <p className="notif-empty">Hozircha bildirishnoma yo&apos;q.</p>
          ) : (
            <div className="notif-list">
              {items.map((item) => (
                <div key={item.id} className="notif-item">
                  <span className={`notif-dot notif-dot-${item.type}`} />
                  <div className="notif-item-body">
                    <p>{item.text}</p>
                    <span className="notif-item-time">{formatRelativeTime(item.createdAt)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function formatRelativeTime(ts) {
  const diffSec = Math.max(0, Math.round((Date.now() - ts) / 1000));
  if (diffSec < 5) return "hozir";
  if (diffSec < 60) return `${diffSec} soniya oldin`;
  const diffMin = Math.round(diffSec / 60);
  if (diffMin < 60) return `${diffMin} daqiqa oldin`;
  const diffHour = Math.round(diffMin / 60);
  if (diffHour < 24) return `${diffHour} soat oldin`;
  const diffDay = Math.round(diffHour / 24);
  return `${diffDay} kun oldin`;
}
