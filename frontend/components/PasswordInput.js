"use client";

import { useState } from "react";
import { Eye, EyeOff } from "./Icons";

/**
 * Parol maydoni — o'ng tomonda ko'z tugmasi bo'lib, foydalanuvchi
 * nima yozganini tekshira olishi uchun matnni ochib-yopadi.
 */
export default function PasswordInput({
  value,
  onChange,
  placeholder = "Parol",
  minLength = 4,
  autoComplete = "current-password",
  required = true,
  id,
}) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="password-wrap">
      <input
        id={id}
        type={visible ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        minLength={minLength}
        autoComplete={autoComplete}
        required={required}
      />
      <button
        type="button"
        className="eye-btn"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? "Parolni yashirish" : "Parolni ko'rsatish"}
        title={visible ? "Parolni yashirish" : "Parolni ko'rsatish"}
        tabIndex={-1}
      >
        {visible ? <EyeOff /> : <Eye />}
      </button>
    </div>
  );
}
