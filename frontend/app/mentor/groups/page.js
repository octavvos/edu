"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import AppShell from "../../../components/AppShell";
import { Calendar, Swap, Users, X } from "../../../components/Icons";
import { useNotify } from "../../../components/NotificationProvider";
import { errorMessage, mentorApi } from "../../../lib/api";
import { initials, useAuth } from "../../../lib/auth";

/** Mentor guruhlari: a'zolar ro'yxati va o'quvchini boshqa guruhga ko'chirish. */
export default function MentorGroupsPage() {
  const { user, loading } = useAuth({ roles: ["mentor"] });
  const notify = useNotify();
  const [groups, setGroups] = useState([]);
  const [activeGroupId, setActiveGroupId] = useState(null);
  const [members, setMembers] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [membersLoading, setMembersLoading] = useState(false);
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    if (loading) return;
    mentorApi
      .groups()
      .then(({ data }) => {
        setGroups(data);
        if (data.length) setActiveGroupId(data[0].id);
      })
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }))
      .finally(() => setDataLoading(false));
  }, [loading, notify]);

  const loadMembers = useCallback((groupId) => {
    if (!groupId) return Promise.resolve();
    setMembersLoading(true);
    return mentorApi
      .members(groupId)
      .then(({ data }) => setMembers(data))
      .catch((err) => notify({ type: "danger", text: errorMessage(err) }))
      .finally(() => setMembersLoading(false));
  }, [notify]);

  useEffect(() => {
    loadMembers(activeGroupId);
  }, [activeGroupId, loadMembers]);

  const activeGroup = groups.find((g) => g.id === activeGroupId);

  async function handleTransfer(membership, toGroupId) {
    if (!toGroupId) return;
    setBusyId(membership.id);
    try {
      await mentorApi.transfer(membership.student.id, activeGroupId, toGroupId);
      const target = groups.find((g) => g.id === toGroupId);
      notify({
        type: "success",
        text: `${membership.student.display_name} → "${target?.name}" guruhiga ko'chirildi`,
      });
      await loadMembers(activeGroupId);
    } catch (err) {
      notify({ type: "danger", text: errorMessage(err) });
    } finally {
      setBusyId(null);
    }
  }

  async function handleRemove(membership) {
    if (!window.confirm(`${membership.student.display_name} guruhdan chiqarilsinmi?`)) return;
    setBusyId(membership.id);
    try {
      await mentorApi.remove(activeGroupId, membership.student.id);
      notify({ type: "info", text: `${membership.student.display_name} guruhdan chiqarildi` });
      await loadMembers(activeGroupId);
    } catch (err) {
      notify({ type: "danger", text: errorMessage(err) });
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <div className="app-shell"><main><div className="skeleton" style={{ height: 200 }} /></main></div>;

  return (
    <AppShell user={user}>
      <div className="page-head">
        <div>
          <h1>Guruhlarim</h1>
          <p>O&apos;quvchilarni ko&apos;ring va kerak bo&apos;lsa boshqa guruhga ko&apos;chiring</p>
        </div>
      </div>

      {dataLoading ? (
        <div className="skeleton" style={{ height: 220 }} />
      ) : groups.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div className="empty-icon"><Users /></div>
            <h3>Sizga guruh biriktirilmagan</h3>
            <p>Manager sizni guruhga mentor qilib tayinlashi kerak.</p>
          </div>
        </div>
      ) : (
        <>
          <div className="row mb-3" style={{ gap: 8 }}>
            {groups.map((group) => (
              <button
                key={group.id}
                className={`btn btn-sm ${group.id === activeGroupId ? "" : "btn-ghost"}`}
                onClick={() => setActiveGroupId(group.id)}
              >
                {group.name}
                <span className="badge badge-neutral" style={{ marginLeft: 4 }}>
                  {group.active_members_count}
                </span>
              </button>
            ))}
          </div>

          {activeGroup && (
            <div className="card mb-3">
              <div className="row-between" style={{ gap: 20, alignItems: "flex-end" }}>
                <div className="row" style={{ gap: 20 }}>
                  <div>
                    <div className="stat-label">Kurs</div>
                    <div className="strong mt-1">{activeGroup.course_title}</div>
                  </div>
                  <div>
                    <div className="stat-label">Sig&apos;im</div>
                    <div className="strong mt-1">
                      {activeGroup.active_members_count} / {activeGroup.capacity}
                    </div>
                  </div>
                  <div>
                    <div className="stat-label">Jadval</div>
                    <div className="strong mt-1 small">
                      {activeGroup.schedules.length
                        ? activeGroup.schedules
                            .map((s) => `${s.weekday_label} ${s.start_time.slice(0, 5)}`)
                            .join(" · ")
                        : "—"}
                    </div>
                  </div>
                </div>

                <Link href={`/mentor/groups/${activeGroup.id}/attendance`} className="btn btn-sm">
                  <Calendar width={15} height={15} />
                  Davomat olish
                </Link>
              </div>
            </div>
          )}

          {membersLoading ? (
            <div className="skeleton" style={{ height: 180 }} />
          ) : members.length === 0 ? (
            <div className="card">
              <div className="empty">
                <div className="empty-icon"><Users /></div>
                <h3>Guruhda o&apos;quvchi yo&apos;q</h3>
                <p>So&apos;rovlarni tasdiqlaganingizdan keyin o&apos;quvchilar shu yerda ko&apos;rinadi.</p>
              </div>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>O&apos;quvchi</th>
                    <th>Username</th>
                    <th>Qo&apos;shilgan</th>
                    <th style={{ width: 260 }}>Boshqa guruhga ko&apos;chirish</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {members.map((m) => (
                    <tr key={m.id}>
                      <td>
                        <div className="row" style={{ gap: 10, flexWrap: "nowrap" }}>
                          <div className="avatar avatar-sm">{initials(m.student)}</div>
                          <span className="strong">{m.student.display_name}</span>
                        </div>
                      </td>
                      <td className="muted">@{m.student.username}</td>
                      <td className="muted mono small">
                        {new Date(m.joined_at).toLocaleDateString("uz-UZ")}
                      </td>
                      <td>
                        <div className="row" style={{ gap: 6, flexWrap: "nowrap" }}>
                          <Swap width={15} height={15} className="dim" />
                          <select
                            defaultValue=""
                            disabled={busyId === m.id}
                            onChange={(e) => {
                              handleTransfer(m, e.target.value);
                              e.target.value = "";
                            }}
                          >
                            <option value="">Guruhni tanlang…</option>
                            {groups
                              .filter((g) => g.id !== activeGroupId)
                              .map((g) => (
                                <option key={g.id} value={g.id}>
                                  {g.name}
                                </option>
                              ))}
                          </select>
                        </div>
                      </td>
                      <td>
                        <button
                          className="btn btn-danger-ghost btn-sm"
                          onClick={() => handleRemove(m)}
                          disabled={busyId === m.id}
                          title="Guruhdan chiqarish"
                        >
                          <X width={15} height={15} />
                        </button>
                      </td>
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
