"use client";

import { useEffect, useState } from "react";
import { catalogApi } from "../../lib/api";
import CourseCard from "../../components/CourseCard";

export default function CatalogPage() {
  const [courses, setCourses] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  async function load(q = "") {
    setLoading(true);
    try {
      const { data } = await catalogApi.searchCourses({ q });
      setCourses(data.results || data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <section>
      <h1>Kurslar katalogi</h1>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          load(query);
        }}
        style={{ maxWidth: 420, marginBottom: 24 }}
      >
        <input
          placeholder="Kurs qidirish..." value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </form>

      {loading ? (
        <p>Yuklanmoqda...</p>
      ) : courses.length === 0 ? (
        <p>Hech narsa topilmadi.</p>
      ) : (
        <div className="grid">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </section>
  );
}
