"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { Check, Inbox, X } from "../../components/Icons";
import { errorMessage, mentorApi } from "../../lib/api";
import { initials, useAuth } from "../../lib/auth";

/** Mentor paneli: ro'yxatdan o'tish so'rovlarini tasdiqlash / rad etish. */
export default function MentorRequestsPage() {
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const [requests, setRequests] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [message, setMessage] = useState(null);

  const load = useCallback(() => {
    return mentorApi
      .requests()
      .then(({ data }) => setRequests(data))
      .catch((err) => setMessage({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, []);

  useEffect(() => {
    if (!loading) load();
  }, [loading, load]);

  async function handleApprove(request) {
    setBusyId(request.id);
    setMessage(null);
    try {
      await mentorApi.approve(request.id);
      setMessage({
        type: "success",
        text: `${request.student.display_name} "${request.group_name}" guruhiga qo'shildi`,
      });
      await load();
    } catch (err) {
      setMessage({ type: "danger", text: errorMessage(err) });
    } finally {
      setBusyId(null);
    }
  }

  async function handleReject(request) {
    const note = window.prompt("Rad etish sababi (ixtiyoriy):", "");
    if (note === null) return; // foydalanuvchi bekor qildi
    setBusyId(request.id);
    setMessage(null);
    try {
      await mentorApi.reject(request.id, note);
      setMessage({ type: "info", text: `${request.student.display_name} so'rovi rad etildi` });
      await load();
    } catch (err) {
      setMessage({ type: "danger", text: errorMessage(err) });
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Ro&apos;yxatdan o&apos;tish so&apos;rovlari</h1>
          <p>O&apos;quvchi ma&apos;lumotlarini ko&apos;rib chiqing va guruhga qabul qiling</p>
        </div>
        {requests.length > 0 && (
          <span className="badge badge-warning">{requests.length} ta kutilmoqda</span>
        )}
      </div>

      {message && <div className={`alert alert-${message.type}`}>{message.text}</div>}

      {dataLoading ? (
        <div className="stack">
          <div className="skeleton" style={{ height: 88 }} />
          <div className="skeleton" style={{ height: 88 }} />
        </div>
      ) : requests.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Inbox /></div>
            <h3>Yangi so&apos;rov yo&apos;q</h3>
            <p>Yangi o&apos;quvchi ro&apos;yxatdan o&apos;tganda shu yerda ko&apos;rinadi.</p>
          </div>
        </div>
      ) : (
        <div className="stack">
          {requests.map((request) => (
            <article key={request.id} className="card card-hover fade-in">
              <div className="row-between" style={{ alignItems: "flex-start" }}>
                <div className="row" style={{ gap: 13, flexWrap: "nowrap" }}>
                  <div className="avatar">{initials(request.student)}</div>
                  <div>
                    <h3>{request.student.display_name}</h3>
                    <div className="small muted mt-1">
                      @{request.student.username} · {request.group_name}
                      <span className="dim"> ({request.group_code})</span>
                    </div>
                    <div className="row mt-2" style={{ gap: 7 }}>
                      <span className="chip">Ism: {request.student.first_name}</span>
                      <span className="chip">Familiya: {request.student.last_name}</span>
                      <span className="badge badge-warning">Kutilmoqda</span>
                    </div>
                  </div>
                </div>

                <div className="row" style={{ flexWrap: "nowrap" }}>
                  <button
                    className="btn btn-success btn-sm"
                    onClick={() => handleApprove(request)}
                    disabled={busyId === request.id}
                  >
                    {busyId === request.id ? <span className="spinner" /> : <Check width={15} height={15} />}
                    Tasdiqlash
                  </button>
                  <button
                    className="btn btn-danger-ghost btn-sm"
                    onClick={() => handleReject(request)}
                    disabled={busyId === request.id}
                  >
                    <X width={15} height={15} />
                    Rad etish
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </AppShell>
  );
}
