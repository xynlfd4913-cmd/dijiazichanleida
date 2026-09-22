import {
  ArrowPathIcon,
  BellAlertIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { DemoNotice, GradeBadge, PageHeader, Panel, StatusPill } from "@/components/ui";
import { getWatchlistAssets } from "@/lib/api";
import { daysUntil, formatMoney } from "@/lib/format";

export const metadata = { title: "关注列表" };

export default async function WatchlistPage() {
  const assets = await getWatchlistAssets();
  const isWithinLimit = (asset: (typeof assets)[number]) => (
    asset.currentPrice !== null
    && asset.opportunity.maxRecommendedBid !== null
    && asset.currentPrice <= asset.opportunity.maxRecommendedBid
  );
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="变化追踪" title="关注列表" description="重点追踪价格、状态、二拍、再上拍、隐形费用与最大建议价变化。" />
      <DemoNotice />

      <div className="grid gap-3 sm:grid-cols-3">
        <Panel className="p-5"><div className="text-sm text-slate-500">正在关注</div><div className="mt-2 text-2xl font-semibold text-white">{assets.length} 项</div></Panel>
        <Panel className="p-5"><div className="text-sm text-slate-500">发生变化</div><div className="mt-2 text-2xl font-semibold text-amber-200">{assets.filter((item) => item.changeNote).length} 项</div></Panel>
        <Panel className="p-5"><div className="text-sm text-slate-500">仍在建议价内</div><div className="mt-2 text-2xl font-semibold text-signal-300">{assets.filter(isWithinLimit).length} 项</div></Panel>
      </div>

      <div className="space-y-4">
        {assets.map((asset) => {
          const withinLimit = isWithinLimit(asset);
          return (
            <Panel key={asset.id} className="overflow-hidden">
              <div className="flex flex-col gap-4 p-5 sm:p-6 xl:flex-row xl:items-center">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <GradeBadge grade={asset.opportunity.grade} />
                    <StatusPill tone={withinLimit ? "teal" : "rose"}>{withinLimit ? "建议价内" : "已超建议价"}</StatusPill>
                    <span className="text-xs text-slate-500">{asset.sourcePlatform}</span>
                  </div>
                  <Link href={`/assets/${asset.id}`} className="mt-3 block text-lg font-semibold text-white hover:text-signal-200">{asset.title}</Link>
                  <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-500">
                    <span className="inline-flex items-center gap-1.5"><ClockIcon className="h-4 w-4" />{daysUntil(asset.endTime)}截止</span>
                    <span>{asset.city} · {asset.district}</span>
                  </div>
                </div>

                <div className="grid min-w-0 grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4 xl:min-w-[560px]">
                  <div><div className="text-xs text-slate-500">当前价</div><div className="mt-1 font-semibold text-white">{formatMoney(asset.currentPrice)}</div></div>
                  <div><div className="text-xs text-slate-500">最大建议价</div><div className="mt-1 font-semibold text-signal-300">{formatMoney(asset.opportunity.maxRecommendedBid)}</div></div>
                  <div><div className="text-xs text-slate-500">成本上限</div><div className="mt-1 font-semibold text-amber-200">{formatMoney(asset.opportunity.allInCostMax)}</div></div>
                  <div><div className="text-xs text-slate-500">未知费用</div><div className="mt-1 font-semibold text-rose-300">{asset.costs.filter((item) => item.status === "unknown").length} 项</div></div>
                </div>
              </div>
              {asset.changeNote ? (
                <div className="flex items-center gap-2 border-t border-amber-300/10 bg-amber-300/[.04] px-5 py-3 text-sm text-amber-100/80 sm:px-6">
                  <ArrowPathIcon className="h-4 w-4 shrink-0 text-amber-200" /><strong className="font-semibold">最新变化：</strong>{asset.changeNote}
                </div>
              ) : null}
            </Panel>
          );
        })}
      </div>

      <Panel className="p-5 sm:p-6">
        <div className="grid gap-5 md:grid-cols-3">
          <div className="flex gap-3"><BellAlertIcon className="h-5 w-5 shrink-0 text-sky-300" /><div><div className="font-medium text-white">临近截止</div><p className="mt-1 text-sm leading-6 text-slate-500">24 小时内进入重点观察，但不鼓励仓促出价。</p></div></div>
          <div className="flex gap-3"><ShieldCheckIcon className="h-5 w-5 shrink-0 text-signal-300" /><div><div className="font-medium text-white">价格护栏</div><p className="mt-1 text-sm leading-6 text-slate-500">当前价超过最大建议价时立刻标红。</p></div></div>
          <div className="flex gap-3"><ExclamationTriangleIcon className="h-5 w-5 shrink-0 text-amber-200" /><div><div className="font-medium text-white">费用变化</div><p className="mt-1 text-sm leading-6 text-slate-500">未知项确认后自动重算安全空间。</p></div></div>
        </div>
      </Panel>
    </div>
  );
}
