"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { groupsApi } from "../../lib/api";
import { homeRouteFor, logout, useAuth } from "../../lib/auth";
import { Hourglass } from "../../components/Icons";

/** Ro'yxatdan o'tgan, lekin mentor hali tasdiqlamagan o'quvchi ekrani. */
export default function PendingPage() {
  const router = useRouter();
  const { user } = useAuth({ allowPending: true });
  const [request, setRequest] = useState(null);

  // Mentor tasdiqlagan bo'lsa darhol kabinetga o'tkazamiz
  useEffect(() => {
    if (user && !user.is_pending_approval) router.replace(homeRouteFor(user));
  }, [user, router]);

  useEffect(() => {
    if (!user) return;
    groupsApi
      .my()
      .then(({ data }) => setRequest(data.join_request))
      .catch(() => {});
  }, [user]);

  const rejected = request?.status === "rejected";

  return (
    <div className="auth-page">
      <div className="auth-card center fade-in">
        <div
          className="logo-mark"
          style={{
            width: 52,
            height: 52,
            borderRadius: 15,
            margin: "0 auto 18px",
            background: rejected ? "var(--danger)" : "linear-gradient(135deg, var(--warning), #f59e0b)",
          }}
        >
          <Hourglass width={24} height={24} />
        </div>

        {rejected ? (
          <>
            <h1 style={{ fontSize: 21 }}>So&apos;rov rad etildi</h1>
            <p className="muted mt-1">
              Mentor sizning so&apos;rovingizni tasdiqlamadi.
              {request?.review_note ? ` Sabab: ${request.review_note}` : ""}
            </p>
          </>
        ) : (
          <>
            <h1 style={{ fontSize: 21 }}>Mentor tasdig&apos;i kutilmoqda</h1>
            <p className="muted mt-1">
              So&apos;rovingiz mentorga yuborildi. U ma&apos;lumotlaringizni ko&apos;rib chiqib
              sizni guruhga qo&apos;shadi.
            </p>
          </>
        )}

        {request && (
          <div className="card mt-3" style={{ textAlign: "left", background: "var(--bg-subtle)" }}>
            <div className="row-between">
              <span className="small muted">Tanlangan guruh</span>
              <span className="strong small">{request.group_name}</span>
            </div>
            <div className="row-between mt-1">
              <span className="small muted">Holat</span>
              <span className={`badge badge-${rejected ? "danger" : "warning"}`}>
                {rejected ? "Rad etilgan" : "Kutilmoqda"}
              </span>
            </div>
          </div>
        )}

        <div className="row mt-3" style={{ justifyContent: "center" }}>
          <button className="btn btn-ghost" onClick={() => window.location.reload()}>
            Holatni yangilash
          </button>
          <button className="btn btn-ghost" onClick={() => logout(router)}>
            Chiqish
          </button>
        </div>
      </div>
    </div>
  );
}
