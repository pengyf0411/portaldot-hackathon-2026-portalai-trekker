import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PortalAI — Portaldot AI Copilot",
  description: "AI-powered onchain assistant for the Portaldot blockchain. Transfer POT, check balances, and explore the chain through natural language.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
