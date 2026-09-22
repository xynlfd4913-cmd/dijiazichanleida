import type { Metadata } from "next";
import "./globals.css";
import { MobileHeader, MobileNavigation, Sidebar } from "@/components/navigation";

export const metadata: Metadata = {
  title: {
    default: "低价资产雷达",
    template: "%s · 低价资产雷达",
  },
  description: "为有限本金计算全口径成本、安全价差与最大建议出价的本地决策工具。",
  icons: [{ rel: "icon", url: "/favicon.svg", type: "image/svg+xml" }],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-ink-950 text-slate-100 antialiased">
        <Sidebar />
        <MobileHeader />
        <div className="min-h-screen lg:pl-[248px]">
          <main className="mx-auto w-full max-w-[1600px] px-4 pb-24 pt-5 sm:px-6 sm:pt-7 lg:px-8 lg:pb-10 lg:pt-8 xl:px-10">{children}</main>
        </div>
        <MobileNavigation />
      </body>
    </html>
  );
}
