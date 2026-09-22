import {
  ArrowRightIcon,
  BanknotesIcon,
  ClockIcon,
  MapPinIcon,
  ShieldCheckIcon,
  WrenchScrewdriverIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { daysUntil, formatMoney, formatPercent } from "@/lib/format";
import type { Asset } from "@/lib/types";
import { GradeBadge, StatusPill } from "./ui";

export function AssetCard({ asset }: { asset: Asset }) {
  const unknownCount = Math.max(asset.opportunity.unknownCostCount, asset.costs.filter((item) => item.status === "unknown").length);
  const hasBidGuard = asset.currentPrice !== null && asset.opportunity.maxRecommendedBid !== null;
  const overRecommended = hasBidGuard && asset.currentPrice! > asset.opportunity.maxRecommendedBid!;
  return (
    <article className="group relative overflow-hidden rounded-2xl border border-white/[.08] bg-white/[.035] p-5 transition duration-200 hover:-translate-y-0.5 hover:border-signal-400/20 hover:bg-white/[.05] hover:shadow-glow">
      <div className="flex flex-wrap items-center gap-2">
        <GradeBadge grade={asset.opportunity.grade} />
        <StatusPill tone={asset.status === "竞价中" ? "teal" : asset.status === "待核验" ? "amber" : "slate"}>{asset.status}</StatusPill>
        <StatusPill>{asset.sourcePlatform}</StatusPill>
        <span className="ml-auto text-xs text-slate-500">{asset.auctionStage}</span>
      </div>

      <Link href={`/assets/${asset.id}`} className="mt-4 block">
        <h2 className="text-lg font-semibold leading-7 text-white transition group-hover:text-signal-200">{asset.title}</h2>
      </Link>

      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm text-slate-500">
        <span className="inline-flex items-center gap-1.5"><MapPinIcon className="h-4 w-4" />{asset.city} · {asset.district} · {asset.distanceKm}km</span>
        <span className="inline-flex items-center gap-1.5"><ClockIcon className="h-4 w-4" />{daysUntil(asset.endTime)}截止</span>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-x-5 gap-y-4 border-y border-white/[.065] py-4 sm:grid-cols-4">
        <div>
          <div className="text-xs text-slate-500">当前价</div>
          <div className="mt-1 text-lg font-semibold tabular-nums text-white">{formatMoney(asset.currentPrice)}</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">全口径成本</div>
          <div className="mt-1 text-sm font-semibold tabular-nums text-amber-100">{formatMoney(asset.opportunity.allInCostMin)}–{formatMoney(asset.opportunity.allInCostMax)}</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">安全价差</div>
          <div className={`mt-1 text-lg font-semibold tabular-nums ${asset.opportunity.safeMargin !== null && asset.opportunity.safeMargin > 0 ? "text-signal-300" : asset.opportunity.safeMargin === null ? "text-amber-200" : "text-rose-300"}`}>{formatMoney(asset.opportunity.safeMargin, false, "暂无估值")}</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">安全 ROI</div>
          <div className={`mt-1 text-lg font-semibold tabular-nums ${asset.opportunity.safeRoi !== null && asset.opportunity.safeRoi >= 0.2 ? "text-signal-300" : asset.opportunity.safeRoi === null ? "text-amber-200" : "text-rose-300"}`}>{formatPercent(asset.opportunity.safeRoi, "暂无估值")}</div>
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-400">
          <span className={`inline-flex items-center gap-1.5 font-semibold ${!hasBidGuard || overRecommended ? "text-rose-300" : "text-signal-200"}`}>
            <ShieldCheckIcon className="h-4 w-4" />建议最高 {formatMoney(asset.opportunity.maxRecommendedBid, false, "待估值")}
          </span>
          <span className="inline-flex items-center gap-1.5"><WrenchScrewdriverIcon className="h-4 w-4" />技能 {asset.opportunity.skillFitScore}</span>
          <span className="inline-flex items-center gap-1.5"><BanknotesIcon className="h-4 w-4" />生产 {asset.opportunity.productionScore}</span>
          <span className={unknownCount || !asset.opportunity.costEstimateComplete ? "text-amber-200" : "text-slate-500"}>{unknownCount} 项未知费用{!asset.opportunity.costEstimateComplete ? " · 判断暂定" : ""}</span>
        </div>
        <Link href={`/assets/${asset.id}`} className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl bg-white/[.055] px-3 text-sm font-medium text-slate-200 transition hover:bg-signal-400/10 hover:text-signal-200">
          查看成本证据 <ArrowRightIcon className="h-4 w-4" />
        </Link>
      </div>
    </article>
  );
}
