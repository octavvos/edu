"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import AppShell from "../../../../components/AppShell";
import { ChevronLeft, Trophy } from "../../../../components/Icons";
import { useNotify } from "../../../../components/NotificationProvider";
import { errorMessage, mentorApi } from "../../../../lib/api";
import { useAuth } from "../../../../lib/auth";
import { formatDateTime, formatDuration } from "../../../../lib/format";

const MEDAL = ["🥇", "🥈", "🥉"];

/** Bitta guruhga yuborilgan testlar bo'yicha o'quvchilar reytingi. */
export default function GroupResultsPage() {
  const { groupId } = useParams();
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const notify = useNotify();
  const [group, setGroup] = useState(null);
  const [rows, setRows] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    if (loading) return;
    Promise.all([mentorApi.groups(), mentorApi.quizResultLeaderboard(groupId)])
      .then(([groupsRes, leaderboardRes]) => {
        setGroup(groupsRes.data.find((g) => g.id === groupId) || null);
        setRows(leaderboardRes.data);
      })
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [loading, groupId, notify]);

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  return (
    <AppShell user={user}>
      <Link href="/mentor/results" className="row small dim" style={{ gap: 4, textDecoration: "none", marginBottom: 10 }}>
        <ChevronLeft width={14} height={14} /> Guruhlar
      </Link>

      <div className="page-head">
        <div>
          <h1>{group?.name || "Guruh natijalari"}</h1>
          <p>Guruhga yuborilgan testlar bo&apos;yicha o&apos;quvchilar reytingi</p>
        </div>
      </div>

      {dataLoading ? (
        <div className="skeleton mt-3" style={{ height: 260 }} />
      ) : rows.length === 0 ? (
        <div className="card mt-3">
          <div className="empty">
            <div className="empty-icon"><Trophy /></div>
            <h3>Bu guruhda hali o&apos;quvchi yo&apos;q</h3>
          </div>
        </div>
      ) : (
        <div className="table-wrap mt-3">
          <table>
            <thead>
              <tr>
                <th style={{ width: 60 }}>O&apos;rin</th>
                <th>O&apos;quvchi</th>
                <th style={{ width: 110 }}>Yechgan</th>
                <th style={{ width: 120 }}>O&apos;rtacha ball</th>
                <th style={{ width: 120 }}>Sarflagan vaqt</th>
                <th style={{ width: 150 }}>Oxirgi faollik</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.student_id}>
                  <td className="strong">{MEDAL[row.rank - 1] || `#${row.rank}`}</td>
                  <td>
                    <Link href={`/mentor/results/${groupId}/students/${row.student_id}`} style={{ color: "inherit" }}>
                      {row.display_name}
                      <span className="dim" style={{ marginLeft: 6 }}>@{row.username}</span>
                    </Link>
                  </td>
                  <td>{row.tests_solved}/{row.tests_assigned}</td>
                  <td className="strong">{row.avg_score !== null ? `${row.avg_score}%` : "—"}</td>
                  <td>{formatDuration(row.total_time_seconds)}</td>
                  <td className="small dim">{formatDateTime(row.last_activity)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
