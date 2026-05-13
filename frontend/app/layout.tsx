import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "Focus Guardian — フォーカス・ガーディアン",
  description: "AIで集中力を守り抜くライフ・オペレーティングシステム",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
