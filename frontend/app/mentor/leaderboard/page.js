"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../../components/AppShell";
import { Trophy, Users } from "../../../components/Icons";
import { errorMessage, mentorApi } from "../../../lib/api";
import { useAuth } from "../../../lib/auth";

const MEDAL = ["🥇", "🥈", "🥉"];

/** Guruh reytingi — baholangan ballar yig'indisi bo'yicha o'quvchilar tartibi. */
export default function MentorLeaderboardPage() {
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const [groups, setGroups] = useState([]);
  const [groupId, setGroupId] = useState(null);
  const [rows, setRows] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    if (loading) return;
    mentorApi
      .groups()
      .then(({ data }) => {
        setGroups(data);
        setGroupId((prev) => prev || data[0]?.id || null);
      })
      .catch((err) => setMessage({ type: "danger", text: errorMessage(err) }));
  }, [loading]);

  const loadLeaderboard = useCallback((id) => {
    if (!id) return;
    setDataLoading(true);
    return mentorApi
      .groupLeaderboard(id)
      .then(({ data }) => setRows(data))
      .catch((err) => setMessage({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, []);

  useEffect(() => {
    if (groupId) loadLeaderboard(groupId);
  }, [groupId, loadLeaderboard]);

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Reyting</h1>
          <p>Baholangan ballar yig&apos;indisi bo&apos;yicha guruh o&apos;quvchilari tartibi</p>
        </div>
      </div>

      {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}

      {groups.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Users /></div>
            <h3>Sizga guruh biriktirilmagan</h3>
          </div>
        </div>
      ) : (
        <>
          {groups.length > 1 && (
            <div className="row mb-3" style={{ gap: 8 }}>
              {groups.map((g) => (
                <button
                  key={g.id}
                  className={`btn btn-sm ${g.id === groupId ? "" : "btn-ghost"}`}
                  onClick={() => setGroupId(g.id)}
                >
                  {g.name}
                </button>
              ))}
            </div>
          )}

          {dataLoading ? (
            <div className="skeleton" style={{ height: 260 }} />
          ) : rows.length === 0 ? (
            <div className="card">
              <div className="empty">
                <div className="empty-icon"><Trophy /></div>
                <h3>Bu guruhda hali o&apos;quvchi yo&apos;q</h3>
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
                  {rows.map((row) => (
                    <tr key={row.student_id}>
                      <td className="strong">{MEDAL[row.rank - 1] || `#${row.rank}`}</td>
                      <td>
                        {row.display_name}
                        <span className="dim" style={{ marginLeft: 6 }}>@{row.username}</span>
                      </td>
                      <td>{row.graded_count}</td>
                      <td className="strong">{row.total_score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}
