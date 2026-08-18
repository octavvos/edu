"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "../../../components/AppShell";
import { Book, ChevronRight, Clock } from "../../../components/Icons";
import { errorMessage, mentorApi } from "../../../lib/api";
import { useAuth } from "../../../lib/auth";

const HOURS_PER_LESSON = 2; // TZ bo'yicha barcha darslar bir xil davomiylikda

/** Mentorga biriktirilgan o'quv kurslari ro'yxati. */
export default function MentorCoursesPage() {
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const [courses, setCourses] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (loading) return;
    mentorApi
      .courses()
      .then(({ data }) => setCourses(data))
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setDataLoading(false));
  }, [loading]);

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Kurslar</h1>
          <p>O&apos;quv kurslari va ularning dars rejasi</p>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {dataLoading ? (
        <div className="grid">
          <div className="skeleton" style={{ height: 140 }} />
          <div className="skeleton" style={{ height: 140 }} />
        </div>
      ) : courses.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Book /></div>
            <h3>Sizga kurs biriktirilmagan</h3>
            <p>Manager sizni biror guruhga mentor qilib tayinlashi kerak.</p>
          </div>
        </div>
      ) : (
        <div className="grid">
          {courses.map((course) => {
            const lessonCount = course.modules.reduce((sum, m) => sum + m.lessons.length, 0);
            return (
              <Link
                key={course.id}
                href={`/mentor/courses/${course.id}`}
                className="card card-hover"
                style={{ display: "block", color: "inherit" }}
              >
                <div className="row-between" style={{ alignItems: "flex-start" }}>
                  <h3>{course.title}</h3>
                  <ChevronRight width={18} height={18} className="dim" />
                </div>
                <div className="row mt-2" style={{ gap: 7 }}>
                  <span className="chip">
                    <Book width={13} height={13} /> {course.modules.length} bo&apos;lim
                  </span>
                  <span className="chip">{lessonCount} ta dars</span>
                  <span className="chip">
                    <Clock width={13} height={13} /> {lessonCount * HOURS_PER_LESSON} soat
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}
