"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getTokens } from "../../lib/api";

export default function TeacherDashboardPage() {
  const router = useRouter();
  const [courses, setCourses] = useState([]);
  const [payouts, setPayouts] = useState({ balance: "0", requests: [] });

  useEffect(() => {
    const { access } = getTokens();
    if (!access) {
      router.push("/login");
      return;
    }
    api.get("/teacher/courses/").then(({ data }) => setCourses(data.results || data));
    api.get("/teacher/payouts/").then(({ data }) => setPayouts(data));
  }, [router]);

  async function createCourse() {
    const title = prompt("Kurs nomi (o'zbekcha):");
    if (!title) return;
    await api.post("/teacher/courses/", { title: { uz: title } });
    const { data } = await api.get("/teacher/courses/");
    setCourses(data.results || data);
  }

  return (
    <section>
      <h1>O&apos;qituvchi kabineti</h1>

      <div className="card" style={{ maxWidth: 320, marginBottom: 24 }}>
        <p>Joriy balans</p>
        <p style={{ fontSize: 24, fontWeight: 700 }}>{payouts.balance} UZS</p>
      </div>

      <button className="btn" onClick={createCourse} style={{ marginBottom: 20 }}>
        + Yangi kurs
      </button>

      <div className="grid">
        {courses.map((course) => (
          <div key={course.id} className="card">
            <strong>{course.title?.uz}</strong>
            <p style={{ fontSize: 13, color: "var(--color-muted)" }}>
              Holat: {course.status} · {course.enrollment_count} o&apos;quvchi
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
