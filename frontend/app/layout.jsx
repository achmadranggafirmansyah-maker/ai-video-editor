import "./globals.css";

export const metadata = {
  title: "AI Video Editor",
  description: "AI-assisted social video editing workspace",
};

export default function RootLayout({ children }) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
