"use client";

import { AdjustmentsHorizontalIcon, MagnifyingGlassIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { useMemo, useState } from "react";
import type { Asset } from "@/lib/types";
import { AssetCard } from "./asset-card";

const categoryOptions = ["全部", "机器设备", "工具", "库存", "商用设备", "电脑", "车辆"];
const stageOptions = ["全部", "一拍", "二拍", "变卖", "清仓"];
const gradeOptions = ["全部", "S", "A", "B", "C", "Skip"];

export function RadarClient({ assets, assetBudget }: { assets: Asset[]; assetBudget: number }) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("全部");
  const [stage, setStage] = useState("全部");
  const [grade, setGrade] = useState("全部");
  const [capitalOnly, setCapitalOnly] = useState(true);
  const [productionOnly, setProductionOnly] = useState(false);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return assets.filter((asset) => {
      if (normalized && !`${asset.title}${asset.city}${asset.district}${asset.category}${asset.subcategory}`.toLowerCase().includes(normalized)) return false;
      if (category !== "全部" && asset.category !== category) return false;
      if (stage !== "全部" && asset.auctionStage !== stage) return false;
      if (grade !== "全部" && asset.opportunity.grade !== grade) return false;
      if (
        capitalOnly
        && (
          asset.opportunity.minimumCashRequired === null
          || asset.opportunity.minimumCashRequired > assetBudget
          || asset.opportunity.capitalFitScore <= 0
        )
      ) return false;
      if (productionOnly && asset.opportunity.productionScore < 70) return false;
      return true;
    }).sort((a, b) => b.opportunity.overallScore - a.opportunity.overallScore);
  }, [assets, assetBudget, capitalOnly, category, grade, productionOnly, query, stage]);

  const hasFilters = query || category !== "全部" || stage !== "全部" || grade !== "全部" || !capitalOnly || productionOnly;
  const reset = () => {
    setQuery(""); setCategory("全部"); setStage("全部"); setGrade("全部"); setCapitalOnly(true); setProductionOnly(false);
  };

  const controlClass = "min-h-11 rounded-xl border border-white/[.09] bg-ink-900 px-3 text-sm text-slate-200 outline-none transition focus:border-signal-400/45";

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-white/[.075] bg-white/[.035] p-4 shadow-glow">
        <div className="flex items-center gap-2 text-sm font-semibold text-white"><AdjustmentsHorizontalIcon className="h-5 w-5 text-signal-300" />筛选机会</div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-[minmax(230px,1.5fr)_repeat(3,minmax(130px,.6fr))]">
          <label className="relative">
            <span className="sr-only">搜索资产</span>
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} className={`${controlClass} w-full pl-9`} placeholder="搜索资产、地区或分类" />
          </label>
          <label>
            <span className="sr-only">资产分类</span>
            <select value={category} onChange={(event) => setCategory(event.target.value)} className={`${controlClass} w-full`}>
              {categoryOptions.map((item) => <option key={item} value={item}>{item === "全部" ? "全部分类" : item}</option>)}
            </select>
          </label>
          <label>
            <span className="sr-only">拍卖阶段</span>
            <select value={stage} onChange={(event) => setStage(event.target.value)} className={`${controlClass} w-full`}>
              {stageOptions.map((item) => <option key={item} value={item}>{item === "全部" ? "全部阶段" : item}</option>)}
            </select>
          </label>
          <label>
            <span className="sr-only">机会等级</span>
            <select value={grade} onChange={(event) => setGrade(event.target.value)} className={`${controlClass} w-full`}>
              {gradeOptions.map((item) => <option key={item} value={item}>{item === "全部" ? "全部等级" : item === "Skip" ? "跳过" : `${item} 级`}</option>)}
            </select>
          </label>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button onClick={() => setCapitalOnly(!capitalOnly)} className={`min-h-10 rounded-xl px-3 text-sm ring-1 ring-inset transition ${capitalOnly ? "bg-signal-400/10 text-signal-200 ring-signal-300/25" : "bg-white/[.035] text-slate-400 ring-white/10"}`}>
            {capitalOnly ? "✓ " : ""}只看 {assetBudget.toLocaleString("zh-CN")} 元单笔预算可承受
          </button>
          <button onClick={() => setProductionOnly(!productionOnly)} className={`min-h-10 rounded-xl px-3 text-sm ring-1 ring-inset transition ${productionOnly ? "bg-signal-400/10 text-signal-200 ring-signal-300/25" : "bg-white/[.035] text-slate-400 ring-white/10"}`}>
            {productionOnly ? "✓ " : ""}生产评分 ≥ 70
          </button>
          {hasFilters ? <button onClick={reset} className="ml-auto inline-flex min-h-10 items-center gap-1.5 px-2 text-sm text-slate-500 hover:text-slate-300"><XMarkIcon className="h-4 w-4" />重置</button> : null}
        </div>
      </div>

      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-slate-400">找到 <strong className="font-semibold text-white">{filtered.length}</strong> 个模拟机会，按综合评分排序</p>
        <p className="hidden text-xs text-slate-600 sm:block">评估价折扣不等于安全空间</p>
      </div>

      {filtered.length ? (
        <div className="grid gap-4 2xl:grid-cols-2">
          {filtered.map((asset) => <AssetCard key={asset.id} asset={asset} />)}
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-white/10 px-6 py-16 text-center">
          <div className="text-base font-semibold text-slate-300">没有符合当前条件的资产</div>
          <p className="mt-2 text-sm text-slate-500">可以减少筛选条件，但不要突破生活保障金与单笔暴露上限。</p>
          <button onClick={reset} className="mt-5 min-h-11 rounded-xl bg-signal-400/10 px-4 text-sm font-semibold text-signal-200 ring-1 ring-inset ring-signal-300/20">恢复默认筛选</button>
        </div>
      )}
    </div>
  );
}
