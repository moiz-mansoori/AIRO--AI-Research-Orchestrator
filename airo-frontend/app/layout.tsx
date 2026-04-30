import type { Metadata } from "next";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIRO — AI Research Orchestrator",
  description: "Multi-agent ML automation system dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="antialiased font-sans bg-slate-50 text-slate-800" suppressHydrationWarning>
      <body 
        className="min-h-screen flex flex-col md:flex-row bg-slate-50 overflow-x-hidden"
        suppressHydrationWarning
      >
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <TopBar />
          <main className="flex-1 flex bg-slate-50 relative">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
