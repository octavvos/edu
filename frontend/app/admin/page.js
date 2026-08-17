/**
 * TZ 4.12: MVP'da admin panel Django Admin + django-unfold orqali amalga
 * oshiriladi (backend/apps/*/admin.py). Alohida React SPA admin panel
 * v1.2 bosqichiga qoldirilgan (12-bo'lim). Bu sahifa shunchaki yo'naltiradi.
 */
export default function AdminRedirectPage() {
  const backendOrigin = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/api\/v1\/?$/, "");
  const adminUrl = `${backendOrigin}/admin/`;

  return (
    <section>
      <h1>Admin panel</h1>
      <p>
        MVP bosqichida boshqaruv paneli Django Admin (django-unfold) orqali ishlaydi.
      </p>
      <a className="btn" href={adminUrl}>Admin panelga o&apos;tish</a>
    </section>
  );
}
