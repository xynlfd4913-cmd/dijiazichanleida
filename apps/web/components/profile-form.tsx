"use client";

import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  LockClosedIcon,
  MapPinIcon,
  PlusIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { FormEvent, useMemo, useState } from "react";
import type { UserProfile } from "@/lib/types";
import { formatMoney } from "@/lib/format";
import { Panel, SectionHeading } from "./ui";

const skillOptions = ["木工", "家具安装", "电动工具维修", "电工", "汽修", "机械维修", "电脑维修", "摄影", "短视频", "电商", "五金", "仓储物流", "家装"];
const assetOptions = ["机器设备", "电动工具", "商用设备", "库存", "电脑", "车辆", "房产"];

export function ProfileForm({ initialProfile }: { initialProfile: UserProfile }) {
  const [form, setForm] = useState(initialProfile);
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "local">("idle");
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
  const fieldClass = "mt-2 min-h-11 w-full rounded-xl border border-white/[.09] bg-ink-950/60 px-3.5 text-base text-white outline-none transition placeholder:text-slate-600 focus:border-signal-400/45";

  const capitalUsage = useMemo(() => Math.round((form.maxSingleExposure / Math.max(form.availableCapital, 1)) * 100), [form.availableCapital, form.maxSingleExposure]);

  const toggleSkill = (skill: string) => setForm((current) => ({
    ...current,
    skills: current.skills.includes(skill) ? current.skills.filter((item) => item !== skill) : [...current.skills, skill],
  }));

  const toggleAsset = (asset: string) => setForm((current) => ({
    ...current,
    preferredAssetTypes: current.preferredAssetTypes.includes(asset) ? current.preferredAssetTypes.filter((item) => item !== asset) : [...current.preferredAssetTypes, asset],
  }));

  async function submit(event: FormEvent) {
    event.preventDefault();
    setStatus("saving");
    const locationParts = form.city.split("·").map((item) => item.trim()).filter(Boolean);
    const payload = {
      name: form.name,
      province: locationParts.length > 1 ? locationParts[0] : "湖北",
      city: locationParts.length > 1 ? locationParts.at(-1) : locationParts[0] || "武汉",
      available_capital: form.availableCapital,
      living_reserve: form.livingReserve,
      debt_repayment_fund: form.debtRepaymentFund,
      monthly_new_capital: form.monthlyNewCapital,
      search_radius: form.searchRadius,
      skills: form.skills,
      preferred_asset_types: form.preferredAssetTypes,
      preferred_strategy: form.preferredStrategy,
      max_single_exposure: form.maxSingleExposure,
      storage_available: form.storageAvailable,
      vehicle_available: form.vehicleAvailable,
    };
    try {
      const response = await fetch(`${apiBase}/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error("api unavailable");
      setStatus("saved");
    } catch {
      window.localStorage.setItem("debt-asset-radar-profile", JSON.stringify(form));
      setStatus("local");
    }
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <div className="grid gap-5 xl:grid-cols-[1.15fr_.85fr]">
        <Panel className="p-5 sm:p-6">
          <SectionHeading title="三个账户" detail="资产预算与生存底线必须彻底隔离" />
          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <label className="text-sm text-slate-400">
              可用资产本金
              <input type="number" min="0" step="100" value={form.availableCapital} onChange={(event) => setForm({ ...form, availableCapital: Number(event.target.value) })} className={fieldClass} />
              <span className="mt-2 block text-xs leading-5 text-signal-300">雷达唯一允许调用的预算</span>
            </label>
            <label className="text-sm text-slate-400">
              生活保障金
              <input type="number" min="0" step="100" value={form.livingReserve} onChange={(event) => setForm({ ...form, livingReserve: Number(event.target.value) })} className={`${fieldClass} border-rose-300/15`} />
              <span className="mt-2 flex items-center gap-1.5 text-xs leading-5 text-rose-300"><LockClosedIcon className="h-3.5 w-3.5" />永远不进入资产预算</span>
            </label>
            <label className="text-sm text-slate-400">
              化债账户
              <input type="number" min="0" step="100" value={form.debtRepaymentFund} onChange={(event) => setForm({ ...form, debtRepaymentFund: Number(event.target.value) })} className={fieldClass} />
            </label>
            <label className="text-sm text-slate-400">
              每月新增本金
              <input type="number" min="0" step="100" value={form.monthlyNewCapital} onChange={(event) => setForm({ ...form, monthlyNewCapital: Number(event.target.value) })} className={fieldClass} />
            </label>
          </div>
          <div className="mt-5 rounded-xl border border-white/[.07] bg-white/[.025] p-4">
            <div className="flex items-center justify-between text-sm"><span className="text-slate-400">单笔最大暴露</span><strong className="text-white">{formatMoney(form.maxSingleExposure)} · {capitalUsage}%</strong></div>
            <input type="range" min="0" max={Math.max(form.availableCapital, 100)} step="100" value={Math.min(form.maxSingleExposure, form.availableCapital)} onChange={(event) => setForm({ ...form, maxSingleExposure: Number(event.target.value) })} className="mt-4 w-full accent-teal-400" />
            {capitalUsage > 90 ? <p className="mt-2 flex items-center gap-1.5 text-xs text-amber-200"><ExclamationTriangleIcon className="h-4 w-4" />单笔暴露过高，会显著降低抗风险余量。</p> : null}
          </div>
        </Panel>

        <Panel className="p-5 sm:p-6">
          <SectionHeading title="地区与策略" detail="决定哪些资产先进入你的视野" />
          <div className="mt-6 space-y-5">
            <label className="text-sm text-slate-400">所在城市<input value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} className={fieldClass} /></label>
            <label className="text-sm text-slate-400">搜索半径<input type="number" min="1" max="1000" value={form.searchRadius} onChange={(event) => setForm({ ...form, searchRadius: Number(event.target.value) })} className={fieldClass} /><span className="mt-2 flex items-center gap-1.5 text-xs text-slate-500"><MapPinIcon className="h-3.5 w-3.5" />{form.searchRadius} 公里内优先</span></label>
            <label className="text-sm text-slate-400">偏好策略<select value={form.preferredStrategy} onChange={(event) => setForm({ ...form, preferredStrategy: event.target.value as UserProfile["preferredStrategy"] })} className={fieldClass}><option value="production">生产自用</option><option value="resale">转卖变现</option><option value="hybrid">生产 + 转卖</option></select></label>
            <div className="grid grid-cols-2 gap-3">
              <button type="button" onClick={() => setForm({ ...form, storageAvailable: !form.storageAvailable })} className={`min-h-11 rounded-xl px-3 text-sm ring-1 ring-inset ${form.storageAvailable ? "bg-signal-400/10 text-signal-200 ring-signal-300/25" : "bg-white/[.03] text-slate-500 ring-white/10"}`}>{form.storageAvailable ? "✓ " : ""}有仓储条件</button>
              <button type="button" onClick={() => setForm({ ...form, vehicleAvailable: !form.vehicleAvailable })} className={`min-h-11 rounded-xl px-3 text-sm ring-1 ring-inset ${form.vehicleAvailable ? "bg-signal-400/10 text-signal-200 ring-signal-300/25" : "bg-white/[.03] text-slate-500 ring-white/10"}`}>{form.vehicleAvailable ? "✓ " : ""}有运输车辆</button>
            </div>
          </div>
        </Panel>
      </div>

      <Panel className="p-5 sm:p-6">
        <SectionHeading title="技能标签" detail="同一件资产，会因为你的技能不同得到不同评分" />
        <div className="mt-5 flex flex-wrap gap-2">
          {skillOptions.map((skill) => {
            const selected = form.skills.includes(skill);
            return <button key={skill} type="button" onClick={() => toggleSkill(skill)} className={`inline-flex min-h-10 items-center gap-1.5 rounded-xl px-3 text-sm ring-1 ring-inset transition ${selected ? "bg-signal-400/10 text-signal-200 ring-signal-300/25" : "bg-white/[.025] text-slate-400 ring-white/[.08] hover:text-slate-200"}`}>{selected ? <XMarkIcon className="h-3.5 w-3.5" /> : <PlusIcon className="h-3.5 w-3.5" />}{skill}</button>;
          })}
        </div>
      </Panel>

      <Panel className="p-5 sm:p-6">
        <SectionHeading title="偏好资产类型" detail="这只是排序偏好，不会绕过费用与本金约束" />
        <div className="mt-5 flex flex-wrap gap-2">
          {assetOptions.map((asset) => {
            const selected = form.preferredAssetTypes.includes(asset);
            return <button key={asset} type="button" onClick={() => toggleAsset(asset)} className={`min-h-10 rounded-xl px-3 text-sm ring-1 ring-inset transition ${selected ? "bg-sky-400/10 text-sky-200 ring-sky-300/25" : "bg-white/[.025] text-slate-400 ring-white/[.08]"}`}>{selected ? "✓ " : ""}{asset}</button>;
          })}
        </div>
      </Panel>

      <div className="sticky bottom-[68px] z-20 flex flex-col gap-3 rounded-2xl border border-white/10 bg-ink-900/95 p-3 shadow-2xl backdrop-blur-xl sm:flex-row sm:items-center sm:justify-between lg:bottom-4">
        <div className="px-2 text-sm text-slate-400">
          {status === "saved" ? <span className="inline-flex items-center gap-2 text-signal-300"><CheckCircleIcon className="h-5 w-5" />已保存并重新计算画像</span> : status === "local" ? <span className="inline-flex items-center gap-2 text-amber-200"><CheckCircleIcon className="h-5 w-5" />API 未启动，已暂存到此浏览器</span> : "保存后将影响本金适配、技能与生产评分"}
        </div>
        <button type="submit" disabled={status === "saving"} className="min-h-11 rounded-xl bg-signal-400 px-5 text-sm font-semibold text-ink-950 transition hover:bg-signal-300 disabled:opacity-60">{status === "saving" ? "正在保存…" : "保存用户画像"}</button>
      </div>
    </form>
  );
}
