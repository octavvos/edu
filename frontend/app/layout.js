import "./globals.css";

export const metadata = {
  title: "Onlayn ta'lim platformasi",
  description: "Kurslarni onlayn o'rganing va sertifikat oling",
};

export default function RootLayout({ children }) {
  return (
    <html lang="uz">
      <body>
        <header className="site-header">
          <a href="/" className="logo">EduPlatform</a>
          <nav>
            <a href="/catalog">Kurslar</a>
            <a href="/dashboard">Kabinetim</a>
            <a href="/teacher">O&apos;qituvchi</a>
            <a href="/login">Kirish</a>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
