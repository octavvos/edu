"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { courseApi, paymentApi } from "../../../lib/api";

export default function CourseDetailPage() {
  const { id: slug } = useParams();
  const router = useRouter();
  const [course, setCourse] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    courseApi.detail(slug).then(({ data }) => setCourse(data)).catch(() => setCourse(null));
  }, [slug]);

  async function handleEnroll() {
    setError("");
    setBusy(true);
    try {
      if (course.price > 0) {
        const idempotencyKey = crypto.randomUUID();
        const { data } = await paymentApi.checkout(course.id, "", idempotencyKey);
        if (data.checkout_url) {
          window.location.href = data.checkout_url;
          return;
        }
      } else {
        await courseApi.enroll(slug);
      }
      router.push("/dashboard");
    } catch (err) {
      if (err.response?.status === 401) {
        router.push("/login");
        return;
      }
      setError(err.response?.data?.detail || "Xatolik yuz berdi");
    } finally {
      setBusy(false);
    }
  }

  if (!course) return <p>Yuklanmoqda...</p>;

  const title = course.title?.uz || Object.values(course.title || {})[0];

  return (
    <section>
      <h1>{title}</h1>
      <p style={{ color: "var(--color-muted)" }}>{course.author_name}</p>
      <p>{course.description?.uz}</p>

      <div className="card" style={{ maxWidth: 320, marginBottom: 24 }}>
        <p style={{ fontSize: 22, fontWeight: 700 }}>
          {course.price > 0 ? `${course.price} ${course.currency}` : "Bepul"}
        </p>
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <button className="btn" onClick={handleEnroll} disabled={busy}>
          {busy ? "..." : course.price > 0 ? "Sotib olish" : "Ro'yxatdan o'tish"}
        </button>
      </div>

      <h2>Kurs dasturi</h2>
      {course.modules?.map((module) => (
        <div key={module.id} className="card" style={{ marginBottom: 12 }}>
          <strong>{module.title?.uz}</strong>
          <ul>
            {module.lessons?.map((lesson) => (
              <li key={lesson.id}>
                {lesson.title?.uz} {lesson.is_free_preview && "(bepul sinov)"}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}
