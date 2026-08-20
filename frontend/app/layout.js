import "./globals.css";
import { NotificationProvider } from "../components/NotificationProvider";

export const metadata = {
  title: "EduPlatform — onlayn ta'lim",
  description: "Guruhli onlayn ta'lim platformasi",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f7f8fc" },
    { media: "(prefers-color-scheme: dark)", color: "#0e1016" },
  ],
};

/**
 * Sarlavha/navigatsiya har bir sahifada AppShell orqali render qilinadi,
 * chunki u foydalanuvchi roliga bog'liq — root layout faqat html qobig'i.
 */
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var theme = localStorage.getItem("edu_theme");
    if (theme === "dark" || theme === "light") {
      document.documentElement.setAttribute("data-theme", theme);
    }
  } catch (e) {}
})();
`;

export default function RootLayout({ children }) {
  return (
    <html lang="uz" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>
        <NotificationProvider>{children}</NotificationProvider>
      </body>
    </html>
  );
}
