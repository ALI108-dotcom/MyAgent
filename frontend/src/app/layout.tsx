import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MyAgent - Conversational AI Assistant",
  description: "Production-ready Personal AI Coding Agent",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-slate-950 text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
