import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HypeTrace AI — Social Trend Intelligence",
  description: "AI-powered trend monitoring across Reddit, X, and YouTube",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
