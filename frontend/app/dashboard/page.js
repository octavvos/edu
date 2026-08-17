"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { meApi, getTokens } from "../../lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [profile, setProfile] = useState(null);
  const [courses, setCourses] = useState({ in_progress: [], completed: [] });
  const [certificates, setCertificates] = useState([]);

  useEffect(() => {
    const { access } = getTokens();
    if (!access) {
      router.push("/login");
      return;
    }
    meApi.profile().then(({ data }) => setProfile(data)).catch(() => router.push("/login"));
    meApi.courses().then(({ data }) => setCourses(data));
    meApi.certificates().then(({ data }) => setCertificates(data));
  }, [router]);

  if (!profile) return <p>Yuklanmoqda...</p>;

  return (
    <section>
      <h1>Salom, {profile.full_name || profile.phone || profile.email}</h1>

      <h2>Davom etayotgan kurslar</h2>
      <div className="grid">
        {courses.in_progress.length === 0 && <p>Hozircha yo&apos;q.</p>}
        {courses.in_progress.map((c) => (
          <a key={c.enrollment_id} href={`/learn/${c.enrollment_id}`} className="card" style={{ textDecoration: "none", color: "inherit" }}>
            <strong>{c.course_title?.uz}</strong>
            <p>{c.progress_percent}% tugatildi</p>
          </a>
        ))}
      </div>

      <h2>Tugatilgan kurslar</h2>
      <div className="grid">
        {courses.completed.length === 0 && <p>Hozircha yo&apos;q.</p>}
        {courses.completed.map((c) => (
          <div key={c.enrollment_id} className="card">
            <strong>{c.course_title?.uz}</strong>
            <p>100% tugatildi ✅</p>
          </div>
        ))}
      </div>

      <h2>Sertifikatlarim</h2>
      <div className="grid">
        {certificates.length === 0 && <p>Hozircha yo&apos;q.</p>}
        {certificates.map((cert) => (
          <a key={cert.id} className="card" href={cert.pdf_url} target="_blank" rel="noreferrer" style={{ textDecoration: "none", color: "inherit" }}>
            <strong>{cert.course_title?.uz}</strong>
            <p style={{ fontSize: 12, color: "var(--color-muted)" }}>{cert.code}</p>
          </a>
        ))}
      </div>
    </section>
  );
}
