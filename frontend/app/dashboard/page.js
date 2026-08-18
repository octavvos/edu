"use client";

import { useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { Book, Calendar, Clock, Users } from "../../components/Icons";
import { catalogApi, groupsApi } from "../../lib/api";
import { useAuth } from "../../lib/auth";

/** O'quvchi kabineti: o'z guruhi, dars jadvali va kurslari. */
export default function DashboardPage() {
  const { user, loading } = useAuth();
  const [group, setGroup] = useState(null);
  const [courses, setCourses] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    if (loading) return;
    Promise.all([
      groupsApi.my().then(({ data }) => setGroup(data.group)).catch(() => {}),
      catalogApi
        .courses()
        .then(({ data }) => setCourses(data.results || data))
        .catch(() => {}),
    ]).finally(() => setDataLoading(false));
  }, [loading]);

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
              <div className="stat-label">Kurslar</div>
              <div className="stat-value">{courses.length}</div>
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
                  <Book /> Mening kurslarim
                </span>
              </h2>
            </div>
            {courses.length ? (
              <div className="grid">
                {courses.map((course) => (
                  <article key={course.id} className="card card-hover" style={{ padding: 16 }}>
                    <h3>{course.title}</h3>
                    {course.description && (
                      <p className="small muted mt-1">{course.description}</p>
                    )}
                    <div className="row mt-2">
                      <span className="badge badge-primary">{course.level_display}</span>
                      {course.enrollment_count > 0 && (
                        <span className="chip">{course.enrollment_count} o&apos;quvchi</span>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<Book />}
                title="Kurs topilmadi"
                text="Guruhingizga kurs biriktirilgach shu yerda ko'rinadi."
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
