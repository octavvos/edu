"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { hasRole, initials, logout } from "../lib/auth";
import { LogOut } from "./Icons";
import NotificationBell from "./NotificationBell";
import ThemeToggle from "./ThemeToggle";

const ROLE_LABEL = {
  manager: "Manager",
  mentor: "Mentor",
  student: "O'quvchi",
};

/** Tizimga kirgan foydalanuvchi uchun umumiy sarlavha + kontent qobig'i. */
export default function AppShell({ user, children, narrow = false }) {
  const router = useRouter();
  const pathname = usePathname();

  const links = [];
  if (hasRole(user, "manager")) links.push({ href: "/manager", label: "Guruhlar" });
  if (hasRole(user, "mentor")) {
    links.push({ href: "/mentor", label: "So'rovlar" });
    links.push({ href: "/mentor/courses", label: "Kurslar" });
    links.push({ href: "/mentor/materials", label: "Materiallar" });
    links.push({ href: "/mentor/tests", label: "Testlar" });
    links.push({ href: "/mentor/homework", label: "Uy vazifalari" });
    links.push({ href: "/mentor/students", label: "O'quvchilar" });
    links.push({ href: "/mentor/groups", label: "Guruhlarim" });
    links.push({ href: "/mentor/leaderboard", label: "Reyting" });
  }
  if (!hasRole(user, "manager") && !hasRole(user, "mentor")) {
    links.push({ href: "/dashboard", label: "Kabinetim" });
    links.push({ href: "/assignments", label: "Topshiriqlarim" });
    links.push({ href: "/tests", label: "Testlarim" });
    links.push({ href: "/leaderboard", label: "Reyting" });
  }

  const primaryRole = user?.roles?.[0];

  return (
    <div className="app-shell">
      <header className="site-header">
        <Link href={user ? "/" : "/login"} className="logo">
          <span className="logo-mark">E</span>
          EduPlatform
        </Link>

        <nav className="site-nav">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="nav-link"
              aria-current={pathname === link.href ? "page" : undefined}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="row" style={{ gap: 10, marginLeft: 8 }}>
          <ThemeToggle user={user} />
          {user && (
            <>
              <NotificationBell />
              <div className="row" style={{ gap: 9 }}>
                <div className="avatar avatar-sm">{initials(user)}</div>
                <div style={{ lineHeight: 1.25 }}>
                  <div style={{ fontSize: 13.5, fontWeight: 600 }}>{user.display_name}</div>
                  <div style={{ fontSize: 11.5 }} className="dim">
                    {ROLE_LABEL[primaryRole] || "Foydalanuvchi"}
                  </div>
                </div>
              </div>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => logout(router)}
                title="Chiqish"
                aria-label="Chiqish"
              >
                <LogOut width={15} height={15} />
              </button>
            </>
          )}
        </div>
      </header>

      <main className={narrow ? "main-narrow" : undefined}>{children}</main>
    </div>
  );
}
