"use client";

import {
  BellAlertIcon,
  BookmarkSquareIcon,
  ChartBarSquareIcon,
  ChevronRightIcon,
  Cog6ToothIcon,
  HomeIcon,
  MagnifyingGlassIcon,
  RectangleStackIcon,
  SignalIcon,
  Squares2X2Icon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentType, SVGProps } from "react";

type Icon = ComponentType<SVGProps<SVGSVGElement>>;

const primaryNav: { href: string; label: string; icon: Icon }[] = [
  { href: "/", label: "我的进度", icon: HomeIcon },
  { href: "/radar", label: "低价资产雷达", icon: SignalIcon },
  { href: "/subscriptions", label: "我的订阅", icon: BellAlertIcon },
  { href: "/watchlist", label: "关注列表", icon: BookmarkSquareIcon },
  { href: "/capital", label: "资本阶梯", icon: ChartBarSquareIcon },
];

const secondaryNav: { href: string; label: string; icon: Icon }[] = [
  { href: "/settings", label: "画像设置", icon: Cog6ToothIcon },
  { href: "/admin", label: "系统后台", icon: Squares2X2Icon },
];

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname.startsWith(href);
}

function NavItem({ href, label, icon: Icon }: { href: string; label: string; icon: Icon }) {
  const pathname = usePathname();
  const active = isActive(pathname, href);
  return (
    <Link
      href={href}
      className={`group flex min-h-11 items-center gap-3 rounded-xl px-3 py-2.5 text-[15px] font-medium transition ${
        active
          ? "bg-signal-400/12 text-signal-300 ring-1 ring-inset ring-signal-400/20"
          : "text-slate-400 hover:bg-white/[.045] hover:text-slate-100"
      }`}
    >
      <Icon className={`h-5 w-5 shrink-0 ${active ? "text-signal-400" : "text-slate-500 group-hover:text-slate-300"}`} />
      <span className="flex-1">{label}</span>
      {active ? <ChevronRightIcon className="h-4 w-4 opacity-70" /> : null}
    </Link>
  );
}

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[248px] flex-col border-r border-white/[.07] bg-ink-950/95 px-4 py-5 backdrop-blur-xl lg:flex">
      <Link href="/" className="mb-8 flex items-center gap-3 px-2" aria-label="低价资产雷达首页">
        <div className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-signal-400/25 bg-signal-400/10">
          <SignalIcon className="h-6 w-6 text-signal-300" />
          <span className="absolute right-1 top-1 h-1.5 w-1.5 rounded-full bg-amber-300 shadow-[0_0_8px_rgba(252,211,77,.9)]" />
        </div>
        <div>
          <div className="text-[15px] font-semibold tracking-wide text-white">低价资产雷达</div>
          <div className="mt-0.5 text-xs text-slate-500">谨慎计算每一笔本金</div>
        </div>
      </Link>

      <nav className="space-y-1" aria-label="主要导航">
        {primaryNav.map((item) => (
          <NavItem key={item.href} {...item} />
        ))}
      </nav>

      <div className="my-5 border-t border-white/[.06]" />
      <nav className="space-y-1" aria-label="系统导航">
        {secondaryNav.map((item) => (
          <NavItem key={item.href} {...item} />
        ))}
      </nav>

      <div className="mt-auto rounded-2xl border border-amber-300/15 bg-amber-300/[.045] p-4">
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[.15em] text-amber-200">
          <RectangleStackIcon className="h-4 w-4" />
          本金纪律
        </div>
        <p className="text-sm leading-6 text-slate-400">生活保障金不进入竞拍预算。未知费用也绝不按 0 计算。</p>
      </div>
    </aside>
  );
}

export function MobileNavigation() {
  const pathname = usePathname();
  const items = [primaryNav[0], primaryNav[1], primaryNav[2], primaryNav[3], primaryNav[4]];
  return (
    <nav className="fixed inset-x-0 bottom-0 z-50 grid grid-cols-5 border-t border-white/[.08] bg-ink-950/95 px-1 pb-[max(env(safe-area-inset-bottom),.35rem)] pt-1.5 backdrop-blur-xl lg:hidden" aria-label="移动端导航">
      {items.map(({ href, label, icon: Icon }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            className={`flex min-h-[52px] flex-col items-center justify-center gap-1 rounded-lg px-1 text-[11px] ${
              active ? "text-signal-300" : "text-slate-500"
            }`}
          >
            <Icon className="h-5 w-5" />
            <span>{label.replace("我的", "")}</span>
          </Link>
        );
      })}
    </nav>
  );
}

export function MobileHeader() {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-white/[.07] bg-ink-950/90 px-4 backdrop-blur-xl lg:hidden">
      <Link href="/" className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-signal-400/10 ring-1 ring-inset ring-signal-400/25">
          <SignalIcon className="h-5 w-5 text-signal-300" />
        </span>
        <span className="font-semibold text-white">低价资产雷达</span>
      </Link>
      <Link href="/settings" className="rounded-xl border border-white/10 p-2.5 text-slate-300" aria-label="打开设置">
        <Cog6ToothIcon className="h-5 w-5" />
      </Link>
    </header>
  );
}

export function PageSearch() {
  return (
    <div className="relative hidden w-[280px] xl:block">
      <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
      <input
        className="w-full rounded-xl border border-white/[.08] bg-white/[.035] py-2.5 pl-9 pr-3 text-sm text-slate-200 outline-none placeholder:text-slate-600 focus:border-signal-400/40"
        placeholder="搜索模拟资产"
        aria-label="搜索模拟资产"
      />
    </div>
  );
}
