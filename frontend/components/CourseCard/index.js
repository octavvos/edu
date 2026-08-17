export default function CourseCard({ course }) {
  const title = course.title?.uz || Object.values(course.title || {})[0] || "Nomsiz kurs";
  return (
    <a href={`/courses/${course.slug || course.id}`} className="card" style={{ textDecoration: "none", color: "inherit" }}>
      <h3>{title}</h3>
      <p style={{ color: "var(--color-muted)" }}>
        {course.price > 0 ? `${course.price} ${course.currency || "UZS"}` : "Bepul"}
      </p>
      <p style={{ fontSize: 13, color: "var(--color-muted)" }}>
        ⭐ {course.rating_avg?.toFixed?.(1) ?? course.rating_avg ?? 0} ({course.rating_count ?? 0})
      </p>
    </a>
  );
}
