"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import PasswordInput from "../../../components/PasswordInput";
import { authApi, errorMessage, groupsApi, setCachedUser, setTokens } from "../../../lib/api";

const MIN_LEN = 4;

export default function RegisterPage() {
  const router = useRouter();
  const [groups, setGroups] = useState([]);
  const [groupsLoading, setGroupsLoading] = useState(true);

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    username: "",
    password: "",
    group_id: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    groupsApi
      .open()
      .then(({ data }) => setGroups(data))
      .catch(() => setError("Guruhlar ro'yxatini yuklab bo'lmadi"))
      .finally(() => setGroupsLoading(false));
  }, []);

  function update(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (!form.group_id) {
      setError("Iltimos, guruhni tanlang");
      return;
    }
    if (form.username.trim().length < MIN_LEN) {
      setError(`Username kamida ${MIN_LEN} ta belgidan iborat bo'lishi kerak`);
      return;
    }
    if (form.password.length < MIN_LEN) {
      setError(`Parol kamida ${MIN_LEN} ta belgidan iborat bo'lishi kerak`);
      return;
    }

    setLoading(true);
    try {
      const { data } = await authApi.register({
        ...form,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        username: form.username.trim(),
      });
      setTokens(data);
      setCachedUser(data.user);
      // Ro'yxatdan o'tgach mentor tasdig'ini kutish ekraniga o'tamiz
      router.replace("/pending");
    } catch (err) {
      setError(errorMessage(err, "Ro'yxatdan o'tishda xatolik yuz berdi"));
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card auth-card-wide fade-in">
        <div className="auth-head">
          <div className="logo-mark">E</div>
          <h1>Ro&apos;yxatdan o&apos;tish</h1>
          <p>Ma&apos;lumotlaringizni kiriting va guruhni tanlang</p>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field-row">
            <div className="field">
              <label htmlFor="first_name">Ism</label>
              <input
                id="first_name"
                type="text"
                value={form.first_name}
                onChange={(e) => update("first_name", e.target.value)}
                placeholder="Jasur"
                autoComplete="given-name"
                autoFocus
                required
              />
            </div>
            <div className="field">
              <label htmlFor="last_name">Familiya</label>
              <input
                id="last_name"
                type="text"
                value={form.last_name}
                onChange={(e) => update("last_name", e.target.value)}
                placeholder="Toshmatov"
                autoComplete="family-name"
                required
              />
            </div>
          </div>

          <div className="field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={form.username}
              onChange={(e) => update("username", e.target.value)}
              placeholder="jasur_t"
              autoComplete="username"
              minLength={MIN_LEN}
              required
            />
            <span className="field-hint">
              Kamida {MIN_LEN} ta belgi — harf, raqam va . _ - belgilari
            </span>
          </div>

          <div className="field">
            <label htmlFor="password">Parol</label>
            <PasswordInput
              id="password"
              value={form.password}
              onChange={(v) => update("password", v)}
              placeholder="Kamida 4 ta belgi"
              autoComplete="new-password"
              minLength={MIN_LEN}
            />
            <span className="field-hint">
              O&apos;ng tomondagi ko&apos;z belgisi orqali yozganingizni tekshirishingiz mumkin
            </span>
          </div>

          <div className="field">
            <label>Guruhni tanlang</label>
            {groupsLoading ? (
              <div className="stack" style={{ gap: 8 }}>
                <div className="skeleton" style={{ height: 62 }} />
                <div className="skeleton" style={{ height: 62 }} />
              </div>
            ) : groups.length === 0 ? (
              <div className="alert alert-warning" style={{ marginBottom: 0 }}>
                Hozircha ochiq guruh yo&apos;q. Keyinroq urinib ko&apos;ring.
              </div>
            ) : (
              <div className="group-picker">
                {groups.map((group) => (
                  <label key={group.id} className="group-option">
                    <input
                      type="radio"
                      name="group"
                      value={group.id}
                      checked={form.group_id === group.id}
                      onChange={() => update("group_id", group.id)}
                      disabled={!group.has_free_seats}
                    />
                    <div className="row-between">
                      <div>
                        <div className="group-option-name">{group.name}</div>
                        <div className="group-option-meta">{group.course_title}</div>
                      </div>
                      {!group.has_free_seats && <span className="badge badge-danger">To&apos;lgan</span>}
                    </div>
                    {group.schedules.length > 0 && (
                      <div className="group-option-meta" style={{ marginTop: 7 }}>
                        {group.schedules
                          .map((s) => `${s.weekday_label} ${s.start_time.slice(0, 5)}–${s.end_time.slice(0, 5)}`)
                          .join(" · ")}
                      </div>
                    )}
                  </label>
                ))}
              </div>
            )}
          </div>

          <button
            className="btn btn-lg btn-block mt-2"
            type="submit"
            disabled={loading || groupsLoading || groups.length === 0}
          >
            {loading && <span className="spinner" />}
            {loading ? "Yuborilmoqda…" : "Ro'yxatdan o'tish"}
          </button>

          <p className="field-hint center mt-2">
            So&apos;rovingiz mentorga yuboriladi. Mentor tasdiqlagach guruhga qo&apos;shilasiz.
          </p>
        </form>

        <div className="auth-foot">
          Hisobingiz bormi? <Link href="/login">Kirish</Link>
        </div>
      </div>
    </div>
  );
}
