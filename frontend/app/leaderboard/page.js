"use client";

import { useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { Trophy, Users } from "../../components/Icons";
import { errorMessage, studentApi } from "../../lib/api";
import { useAuth } from "../../lib/auth";

const MEDAL = ["🥇", "🥈", "🥉"];

/** O'quvchining o'z guruhi reytingi — baholangan ballar yig'indisi bo'yicha. */
export default function LeaderboardPage() {
  const { user, loading } = useAuth();
  const [data, setData] = useState({ group_name: null, results: [] });
  const [dataLoading, setDataLoading] = useState(true);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    if (loading) return;
    studentApi
      .leaderboard()
      .then(({ data: payload }) => setData(payload))
      .catch((err) => setMessage({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [loading]);

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Reyting</h1>
          <p>{data.group_name ? `${data.group_name} guruhi` : "Baholangan ballar bo'yicha tartib"}</p>
        </div>
      </div>

      {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}

      {dataLoading ? (
        <div className="skeleton" style={{ height: 260 }} />
      ) : !data.group_name ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Users /></div>
            <h3>Guruhga qo&apos;shilmagansiz</h3>
            <p>Mentor sizni guruhga qabul qilgach reyting shu yerda ko&apos;rinadi.</p>
          </div>
        </div>
      ) : data.results.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Trophy /></div>
            <h3>Hali baholangan ish yo&apos;q</h3>
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th style={{ width: 60 }}>O&apos;rin</th>
                <th>O&apos;quvchi</th>
                <th style={{ width: 130 }}>Baholangan ishlar</th>
                <th style={{ width: 110 }}>Jami ball</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((row) => (
                <tr
                  key={row.student_id}
                  style={row.username === user?.username ? { background: "var(--primary-soft)" } : undefined}
                >
                  <td className="strong">{MEDAL[row.rank - 1] || `#${row.rank}`}</td>
                  <td>
                    {row.display_name}
                    {row.username === user?.username && (
                      <span className="chip" style={{ marginLeft: 6 }}>Siz</span>
                    )}
                  </td>
                  <td>{row.graded_count}</td>
                  <td className="strong">{row.total_score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
