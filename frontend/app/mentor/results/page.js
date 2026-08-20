"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "../../../components/AppShell";
import { Trophy, Users } from "../../../components/Icons";
import { useNotify } from "../../../components/NotificationProvider";
import { errorMessage, mentorApi } from "../../../lib/api";
import { useAuth } from "../../../lib/auth";

/** Test yuborilgan guruhlar ro'yxati — har biri uchun umumiy o'zlashtirish ko'rsatkichi. */
export default function MentorResultsPage() {
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const notify = useNotify();
  const [rows, setRows] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    if (loading) return;
    mentorApi
      .quizResultGroups()
      .then(({ data }) => setRows(data))
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [loading, notify]);

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Natijalar</h1>
          <p>Test yuborilgan guruhlar va ularning o&apos;zlashtirish ko&apos;rsatkichi</p>
        </div>
      </div>

      {dataLoading ? (
        <div className="stack mt-3">
          <div className="skeleton" style={{ height: 90 }} />
          <div className="skeleton" style={{ height: 90 }} />
        </div>
      ) : rows.length === 0 ? (
        <div className="card mt-3">
          <div className="empty">
            <div className="empty-icon"><Trophy /></div>
            <h3>Hozircha natija yo&apos;q</h3>
            <p>Guruhga test yuborilgach, bu yerda natijalar ko&apos;rinadi.</p>
          </div>
        </div>
      ) : (
        <div className="stack mt-3" style={{ gap: 10 }}>
          {rows.map((row) => (
            <Link key={row.group_id} href={`/mentor/results/${row.group_id}`} className="card row-between" style={{ textDecoration: "none", color: "inherit" }}>
              <div className="row" style={{ gap: 10 }}>
                <div className="empty-icon" style={{ width: 38, height: 38, minWidth: 38 }}><Users width={17} height={17} /></div>
                <div>
                  <div className="strong">{row.group_name}</div>
                  <div className="small dim">{row.course_title}</div>
                </div>
              </div>
              <div className="row" style={{ gap: 22 }}>
                <Stat label="Test" value={row.tests_sent} />
                <Stat label="O'quvchi" value={row.student_count} />
                <Stat label="O'rtacha ball" value={row.avg_score !== null ? `${row.avg_score}%` : "—"} />
                <Stat label="Bajarilgan" value={`${row.completion_percent}%`} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  );
}

function Stat({ label, value }) {
  return (
    <div style={{ textAlign: "right" }}>
      <div className="strong">{value}</div>
      <div className="small dim">{label}</div>
    </div>
  );
}
