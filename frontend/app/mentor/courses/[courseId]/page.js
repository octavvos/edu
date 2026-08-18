"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import AppShell from "../../../../components/AppShell";
import CourseSyllabus from "../../../../components/mentor/CourseSyllabus";
import { ChevronRight } from "../../../../components/Icons";
import { errorMessage, mentorApi } from "../../../../lib/api";
import { useAuth } from "../../../../lib/auth";

/** Bitta kursning to'liq dars rejasi — mentor shu yerda materiallarni boshqaradi. */
export default function MentorCourseDetailPage() {
  const { courseId } = useParams();
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const [course, setCourse] = useState(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [message, setMessage] = useState(null);

  const load = useCallback(() => {
    return mentorApi
      .courses()
      .then(({ data }) => {
        const found = data.find((c) => c.id === courseId);
        setCourse(found || null);
        if (!found) setMessage({ type: "danger", text: "Kurs topilmadi yoki sizga biriktirilmagan" });
      })
      .catch((err) => setMessage({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [courseId]);

  useEffect(() => {
    if (!loading) load();
  }, [loading, load]);

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  return (
    <AppShell user={user}>
      <div className="row small mb-2" style={{ gap: 6 }}>
        <Link href="/mentor/courses" className="muted">Kurslar</Link>
        <ChevronRight width={13} height={13} className="dim" />
        <span className="strong">{course?.title || "…"}</span>
      </div>

      <div className="page-head">
        <div>
          <h1>{course?.title || "Dars rejasi"}</h1>
          <p>Modul va darslarni boshqaring, material yuklang, test oching</p>
        </div>
      </div>

      {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}

      {dataLoading ? (
        <div className="skeleton" style={{ height: 320 }} />
      ) : course ? (
        <CourseSyllabus course={course} onChanged={load} onError={setMessage} />
      ) : null}
    </AppShell>
  );
}
