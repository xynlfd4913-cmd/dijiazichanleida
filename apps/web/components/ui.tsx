import {
  ArrowDownRightIcon,
  ArrowTrendingUpIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  QuestionMarkCircleIcon,
} from "@heroicons/react/24/outline";
import type { ReactNode } from "react";
import type { CostStatus } from "@/lib/types";

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex min-w-0 flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
      <div className="min-w-0">
        {eyebrow ? <p className="mb-2 text-xs font-semibold uppercase tracking-[.18em] text-signal-400">{eyebrow}</p> : null}
        <h1 className="text-balance text-2xl font-semibold tracking-tight text-white sm:text-3xl">{title}</h1>
        {description ? <p className="mt-2 max-w-3xl text-[15px] leading-6 text-slate-400">{description}</p> : null}
      </div>
      {action ? <div className="w-full min-w-0 xl:w-auto xl:shrink-0">{action}</div> : null}
    </div>
  );
}

export function DemoNotice() {
  return (
    <div className="flex items-start gap-2.5 rounded-xl border border-sky-400/15 bg-sky-400/[.055] px-3.5 py-2.5 text-sm text-sky-100/80">
      <InformationCircleIcon className="mt-0.5 h-4 w-4 shrink-0 text-sky-300" />
      <span><strong className="font-semibold text-sky-200">Phase 0 演示环境</strong> · 当前全部为模拟数据，未连接、未抓取任何真实拍卖网站。</span>
    </div>
  );
}

export function GradeBadge({ grade }: { grade: "S" | "A" | "B" | "C" | "Skip" }) {
  const styles = {
    S: "border-teal-300/30 bg-teal-300/15 text-teal-200",
    A: "border-emerald-300/25 bg-emerald-300/10 text-emerald-200",
    B: "border-sky-300/25 bg-sky-300/10 text-sky-200",
    C: "border-amber-300/25 bg-amber-300/10 text-amber-200",
    Skip: "border-rose-300/25 bg-rose-300/10 text-rose-200",
  };
  return (
    <span className={`inline-flex items-center rounded-lg border px-2.5 py-1 text-xs font-bold ${styles[grade]}`}>
      {grade === "Skip" ? "跳过" : `${grade} 级`}
    </span>
  );
}

export function StatusPill({ children, tone = "slate" }: { children: ReactNode; tone?: "teal" | "amber" | "rose" | "sky" | "slate" }) {
  const tones = {
    teal: "bg-teal-400/10 text-teal-200 ring-teal-300/20",
    amber: "bg-amber-400/10 text-amber-200 ring-amber-300/20",
    rose: "bg-rose-400/10 text-rose-200 ring-rose-300/20",
    sky: "bg-sky-400/10 text-sky-200 ring-sky-300/20",
    slate: "bg-slate-400/10 text-slate-300 ring-slate-300/15",
  };
  return <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${tones[tone]}`}>{children}</span>;
}

export function Panel({ children, className = "", id }: { children: ReactNode; className?: string; id?: string }) {
  return <section id={id} className={`min-w-0 rounded-2xl border border-white/[.075] bg-white/[.035] shadow-glow ${className}`}>{children}</section>;
}

export function SectionHeading({ title, detail, action }: { title: string; detail?: string; action?: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col items-start justify-between gap-3 sm:flex-row sm:items-center sm:gap-4">
      <div className="min-w-0">
        <h2 className="text-base font-semibold text-white">{title}</h2>
        {detail ? <p className="mt-1 text-sm text-slate-500">{detail}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export function Metric({
  label,
  value,
  detail,
  tone = "neutral",
  icon,
}: {
  label: string;
  value: string;
  detail?: string;
  tone?: "neutral" | "positive" | "warning" | "danger";
  icon?: ReactNode;
}) {
  const colors = {
    neutral: "text-white",
    positive: "text-signal-300",
    warning: "text-amber-200",
    danger: "text-rose-300",
  };
  return (
    <div className="min-w-0">
      <div className="flex items-center gap-2 text-sm text-slate-500">{icon}{label}</div>
      <div className={`mt-2 break-words text-xl font-semibold tabular-nums tracking-tight ${colors[tone]}`}>{value}</div>
      {detail ? <p className="mt-1.5 text-xs leading-5 text-slate-500">{detail}</p> : null}
    </div>
  );
}

export function ScoreBar({ label, score, tone = "teal" }: { label: string; score: number; tone?: "teal" | "amber" | "sky" }) {
  const color = tone === "amber" ? "bg-amber-300" : tone === "sky" ? "bg-sky-300" : "bg-signal-400";
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <span className="font-semibold tabular-nums text-slate-200">{score}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-white/[.07]">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.max(0, Math.min(score, 100))}%` }} />
      </div>
    </div>
  );
}

export function ScoreDial({ score, label }: { score: number; label: string }) {
  const angle = Math.max(0, Math.min(score, 100)) * 3.6;
  return (
    <div className="flex items-center gap-3">
      <div
        className="relative grid h-16 w-16 shrink-0 place-items-center rounded-full"
        style={{ background: `conic-gradient(#2dd4bf ${angle}deg, rgba(255,255,255,.07) ${angle}deg)` }}
      >
        <div className="grid h-[52px] w-[52px] place-items-center rounded-full bg-ink-850">
          <span className="text-lg font-bold tabular-nums text-white">{score}</span>
        </div>
      </div>
      <div>
        <div className="text-sm font-medium text-slate-200">{label}</div>
        <div className="mt-1 text-xs text-slate-500">满分 100</div>
      </div>
    </div>
  );
}

export function CostStatusBadge({ status }: { status: CostStatus }) {
  const content = {
    known: { label: "已知", icon: CheckCircleIcon, style: "bg-teal-400/10 text-teal-200 ring-teal-300/20" },
    estimated: { label: "预计", icon: ExclamationTriangleIcon, style: "bg-amber-400/10 text-amber-200 ring-amber-300/20" },
    unknown: { label: "未知待核验", icon: QuestionMarkCircleIcon, style: "bg-rose-400/10 text-rose-200 ring-rose-300/20" },
  }[status];
  const Icon = content.icon;
  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold ring-1 ring-inset ${content.style}`}>
      <Icon className="h-3.5 w-3.5" />
      {content.label}
    </span>
  );
}

export function Trend({ direction, children }: { direction: "up" | "down"; children: ReactNode }) {
  const Icon = direction === "up" ? ArrowTrendingUpIcon : ArrowDownRightIcon;
  return (
    <span className={`inline-flex items-center gap-1 text-xs ${direction === "up" ? "text-signal-300" : "text-amber-200"}`}>
      <Icon className="h-3.5 w-3.5" />{children}
    </span>
  );
}
