"use client";

import { useEffect, useState } from "react";
import AppShell from "../../../components/AppShell";
import { Users } from "../../../components/Icons";
import { errorMessage, mentorApi } from "../../../lib/api";
import { initials, useAuth } from "../../../lib/auth";

/** O'quvchilar monitoringi: progress, oxirgi faollik va xavf ostidagilar. */
export default function MentorStudentsPage() {
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const [data, setData] = useState({ results: [], at_risk_count: 0, total: 0 });
  const [groups, setGroups] = useState([]);
  const [groupId, setGroupId] = useState("");
  const [onlyRisk, setOnlyRisk] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    if (loading) return;
    mentorApi.groups().then(({ data: g }) => setGroups(g)).catch(() => {});
  }, [loading]);

  useEffect(() => {
    if (loading) return;
    setDataLoading(true);
    mentorApi
      .students(groupId ? { group: groupId } : {})
      .then(({ data: payload }) => setData(payload))
      .catch((err) => setMessage({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [loading, groupId]);

  if (loading) {
    return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;
  }

  const rows = onlyRisk ? data.results.filter((r) => r.at_risk) : data.results;

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>O&apos;quvchilar</h1>
          <p>Progress, faollik va e&apos;tibor talab qiladigan o&apos;quvchilar</p>
        </div>
      </div>

      {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}

      <div className="stats mb-3">
        <div className="stat">
          <div className="stat-label">Jami o&apos;quvchi</div>
          <div className="stat-value">{data.total}</div>
        </div>
        <div className="stat">
          <div className="stat-label">Xavf ostida</div>
          <div className="stat-value" style={{ color: data.at_risk_count ? "var(--danger)" : undefined }}>
            {data.at_risk_count}
          </div>
        </div>
        <div className="stat">
          <div className="stat-label">O&apos;rtacha progress</div>
          <div className="stat-value">
            {data.results.length
              ? Math.round(
                  data.results.reduce((sum, r) => sum + r.progress_percent, 0) / data.results.length,
                )
              : 0}
            %
          </div>
        </div>
      </div>

      <div className="row mb-3" style={{ gap: 8 }}>
        <select value={groupId} onChange={(e) => setGroupId(e.target.value)} style={{ maxWidth: 220 }}>
          <option value="">Barcha guruhlar</option>
          {groups.map((g) => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
        <button
          className={`btn btn-sm ${onlyRisk ? "" : "btn-ghost"}`}
          onClick={() => setOnlyRisk((v) => !v)}
        >
          Faqat xavf ostidagilar
        </button>
      </div>

      {dataLoading ? (
        <div className="skeleton" style={{ height: 220 }} />
      ) : rows.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Users /></div>
            <h3>{onlyRisk ? "Xavf ostidagi o'quvchi yo'q" : "O'quvchi yo'q"}</h3>
            <p>
              {onlyRisk
                ? "Barcha o'quvchilar yaxshi holatda."
                : "So'rovlarni tasdiqlaganingizdan keyin o'quvchilar shu yerda ko'rinadi."}
            </p>
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>O&apos;quvchi</th>
                <th>Guruh</th>
                <th style={{ minWidth: 150 }}>Progress</th>
                <th>Oxirgi kirgan</th>
                <th>Topshiriqlar</th>
                <th>Holat</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div className="row" style={{ gap: 10, flexWrap: "nowrap" }}>
                      <div className="avatar avatar-sm">{initials(r)}</div>
                      <div>
                        <div className="strong">{r.display_name}</div>
                        <div className="small dim">@{r.username}</div>
                      </div>
                    </div>
                  </td>
                  <td className="muted">{r.group_name}</td>
                  <td>
                    <ProgressBar percent={r.progress_percent} />
                    <div className="small dim mt-1">{r.completed_lessons} ta dars</div>
                  </td>
                  <td className="small">{formatLastLogin(r)}</td>
                  <td className="small">
                    {r.pending_submissions > 0 ? (
                      <span className="chip">{r.pending_submissions} ta kutilmoqda</span>
                    ) : (
                      <span className="dim">—</span>
                    )}
                    {r.overdue_submissions > 0 && (
                      <div className="mt-1">
                        <span className="badge badge-danger">
                          {r.overdue_submissions} ta kechikkan
                        </span>
                      </div>
                    )}
                  </td>
                  <td>
                    {r.at_risk ? (
                      <div>
                        <span className="badge badge-danger">Xavf ostida</span>
                        <ul className="small muted mt-1" style={{ margin: 0, paddingLeft: 16 }}>
                          {r.risk_reasons.map((reason) => (
                            <li key={reason}>{reason}</li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      <span className="badge badge-success">Yaxshi</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}

function ProgressBar({ percent }) {
  const color =
    percent >= 70 ? "var(--success)" : percent >= 30 ? "var(--warning)" : "var(--danger)";
  return (
    <div className="row" style={{ gap: 8, flexWrap: "nowrap" }}>
      <div style={{
        flex: 1, height: 7, minWidth: 70,
        background: "var(--bg-subtle)", borderRadius: "var(--radius-full)", overflow: "hidden",
      }}>
        <div style={{
          width: `${Math.min(100, percent)}%`, height: "100%",
          background: color, borderRadius: "var(--radius-full)",
          transition: "width 0.3s var(--ease)",
        }} />
      </div>
      <span className="small mono strong" style={{ minWidth: 36, textAlign: "right" }}>
        {Math.round(percent)}%
      </span>
    </div>
  );
}

function formatLastLogin(row) {
  if (!row.last_login) return <span className="badge badge-danger">Hech qachon</span>;
  const days = row.days_since_login;
  if (days === 0) return "Bugun";
  if (days === 1) return "Kecha";
  return <span className={days >= 14 ? "strong" : "muted"}>{days} kun oldin</span>;
}
