"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { Calendar, Clock, Inbox, Users } from "../../components/Icons";
import { groupsApi, studentApi } from "../../lib/api";
import { useAuth } from "../../lib/auth";

/**
 * O'quvchi kabineti: o'z guruhi va dars jadvali.
 * Kurs kontenti bu yerda ko'rsatilmaydi — o'quvchi faqat mentor jo'natgan
 * vazifani va unga biriktirilgan taqdimotni "Topshiriqlarim" bo'limida ko'radi.
 */
export default function DashboardPage() {
  const { user, loading } = useAuth();
  const [group, setGroup] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    if (loading) return;
    Promise.all([
      groupsApi.my().then(({ data }) => setGroup(data.group)).catch(() => {}),
      studentApi.myAssignments().then(({ data }) => setAssignments(data)).catch(() => {}),
    ]).finally(() => setDataLoading(false));
  }, [loading]);

  const pendingCount = assignments.filter(
    (a) => a.submission?.status !== "accepted",
  ).length;

  if (loading) return <PageSkeleton />;

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Salom, {user?.first_name || user?.username}! 👋</h1>
          <p>Guruhingiz va dars jadvalingiz bilan tanishing</p>
        </div>
      </div>

      {dataLoading ? (
        <div className="stats">
          <div className="skeleton" style={{ height: 84 }} />
          <div className="skeleton" style={{ height: 84 }} />
          <div className="skeleton" style={{ height: 84 }} />
        </div>
      ) : (
        <>
          <div className="stats mb-3">
            <div className="stat">
              <div className="stat-label">Guruhim</div>
              <div className="stat-value" style={{ fontSize: 18, marginTop: 8 }}>
                {group?.name || "—"}
              </div>
            </div>
            <div className="stat">
              <div className="stat-label">Haftalik darslar</div>
              <div className="stat-value">{group?.schedules?.length || 0}</div>
            </div>
            <div className="stat">
              <div className="stat-label">Guruhdoshlar</div>
              <div className="stat-value">{group?.active_members_count ?? 0}</div>
            </div>
            <div className="stat">
              <div className="stat-label">Bajarilmagan vazifa</div>
              <div className="stat-value">{pendingCount}</div>
            </div>
          </div>

          <div className="grid" style={{ gridTemplateColumns: "minmax(0, 1.2fr) minmax(0, 1fr)" }}>
            <section className="card">
              <div className="card-head">
                <h2>
                  <span className="row" style={{ gap: 8 }}>
                    <Calendar /> Dars jadvali
                  </span>
                </h2>
              </div>
              {group?.schedules?.length ? (
                <div className="schedule-list">
                  {group.schedules.map((s) => (
                    <div key={s.id} className="schedule-item">
                      <span className="schedule-day">{s.weekday_label}</span>
                      <span className="schedule-time mono">
                        {s.start_time.slice(0, 5)} – {s.end_time.slice(0, 5)}
                      </span>
                      <span className="spacer" />
                      {s.room && <span className="chip">{s.room}</span>}
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={<Clock />}
                  title="Jadval hali belgilanmagan"
                  text="Manager dars vaqtlarini belgilagach shu yerda ko'rinadi."
                />
              )}
            </section>

            <section className="card">
              <div className="card-head">
                <h2>
                  <span className="row" style={{ gap: 8 }}>
                    <Users /> Guruh
                  </span>
                </h2>
              </div>
              {group ? (
                <div className="stack" style={{ gap: 12 }}>
                  <InfoRow label="Nomi" value={group.name} />
                  <InfoRow label="Kod" value={group.code} />
                  <InfoRow label="Kurs" value={group.course_title} />
                  <InfoRow label="Mentor" value={group.mentor_name || "—"} />
                  <InfoRow
                    label="A'zolar"
                    value={`${group.active_members_count} / ${group.capacity}`}
                  />
                </div>
              ) : (
                <EmptyState
                  icon={<Users />}
                  title="Guruhga qo'shilmagansiz"
                  text="Mentor sizni guruhga qabul qilishi kerak."
                />
              )}
            </section>
          </div>

          <section className="card mt-3">
            <div className="card-head">
              <h2>
                <span className="row" style={{ gap: 8 }}>
                  <Inbox /> Topshiriqlarim
                </span>
              </h2>
              {assignments.length > 0 && (
                <Link href="/assignments" className="btn btn-ghost btn-sm">
                  Hammasi
                </Link>
              )}
            </div>
            {assignments.length ? (
              <div className="stack" style={{ gap: 8 }}>
                {assignments.slice(0, 3).map((a) => (
                  <Link
                    key={a.id}
                    href="/assignments"
                    className="row-between"
                    style={{
                      padding: "11px 13px", background: "var(--bg-subtle)",
                      borderRadius: "var(--radius)", color: "var(--text)",
                    }}
                  >
                    <span className="small strong">{a.lesson_title}</span>
                    {a.submission?.grade ? (
                      <span className="chip">
                        Ball: <strong>{a.submission.grade.score}</strong> / {a.max_score}
                      </span>
                    ) : (
                      <span className="badge badge-info">
                        {a.submission ? "Tekshiruvda" : "Topshirilmagan"}
                      </span>
                    )}
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<Inbox />}
                title="Vazifa yo'q"
                text="Mentoringiz vazifa jo'natgach shu yerda ko'rinadi."
              />
            )}
          </section>
        </>
      )}
    </AppShell>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="row-between">
      <span className="small muted">{label}</span>
      <span className="small strong">{value}</span>
    </div>
  );
}

function EmptyState({ icon, title, text }) {
  return (
    <div className="empty">
      <div className="empty-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

function PageSkeleton() {
  return (
    <div className="app-shell">
      <main>
        <div className="skeleton" style={{ height: 34, width: 260, marginBottom: 24 }} />
        <div className="stats">
          <div className="skeleton" style={{ height: 84 }} />
          <div className="skeleton" style={{ height: 84 }} />
          <div className="skeleton" style={{ height: 84 }} />
        </div>
      </main>
    </div>
  );
}
