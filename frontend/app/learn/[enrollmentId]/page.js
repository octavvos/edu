"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { learnApi } from "../../../lib/api";
import VideoPlayer from "../../../components/VideoPlayer";

export default function LearnPage() {
  const { enrollmentId } = useParams();
  const searchParams = useSearchParams();
  const lessonId = searchParams.get("lesson");

  const [lesson, setLesson] = useState(null);
  const [playback, setPlayback] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!lessonId) return;
    learnApi.lesson(enrollmentId, lessonId).then(({ data }) => setLesson(data)).catch((err) => {
      setError(err.response?.data?.detail || "Darsga kirish rad etildi");
    });
  }, [enrollmentId, lessonId]);

  useEffect(() => {
    if (!lessonId || lesson?.type !== "video") return;
    learnApi.playbackToken(enrollmentId, lessonId).then(({ data }) => setPlayback(data)).catch(() => {});
  }, [enrollmentId, lessonId, lesson]);

  const handleProgress = useCallback(
    ({ position, watched }) => {
      learnApi.updateProgress(enrollmentId, lessonId, {
        seconds_watched: watched, last_position: position, mark_completed: false,
      });
    },
    [enrollmentId, lessonId],
  );

  async function markComplete() {
    await learnApi.updateProgress(enrollmentId, lessonId, {
      seconds_watched: 0, last_position: 0, mark_completed: true,
    });
    alert("Dars tugatilgan deb belgilandi");
  }

  if (!lessonId) return <p>Dars tanlanmagan. ?lesson=&lt;id&gt; parametrini qo&apos;shing.</p>;
  if (error) return <p style={{ color: "crimson" }}>{error}</p>;
  if (!lesson) return <p>Yuklanmoqda...</p>;

  return (
    <section>
      <h1>{lesson.title?.uz}</h1>

      {lesson.type === "video" && playback && (
        <VideoPlayer manifestUrl={playback.manifest_url} watermarkText={playback.watermark_text} onProgress={handleProgress} />
      )}

      {lesson.type === "text" && (
        <div dangerouslySetInnerHTML={{ __html: lesson.text_content?.uz || "" }} />
      )}

      {lesson.type === "file" && lesson.file_asset && (
        <a className="btn" href={lesson.file_asset.original_filename}>Faylni yuklab olish</a>
      )}

      <div style={{ marginTop: 24 }}>
        <button className="btn" onClick={markComplete}>Darsni tugatdim</button>
      </div>
    </section>
  );
}
