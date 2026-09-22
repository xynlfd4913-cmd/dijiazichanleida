"use client";

import {
  BellAlertIcon,
  CheckCircleIcon,
  MapPinIcon,
  PauseCircleIcon,
  PlusIcon,
  SignalIcon,
  WrenchScrewdriverIcon,
} from "@heroicons/react/24/outline";
import { useState } from "react";
import type { Subscription } from "@/lib/types";
import { formatMoney, formatPercent } from "@/lib/format";
import { Panel, StatusPill } from "./ui";

export function SubscriptionList({ initialSubscriptions }: { initialSubscriptions: Subscription[] }) {
  const [items, setItems] = useState(initialSubscriptions);
  const toggle = (id: string) => setItems((current) => current.map((item) => item.id === id ? { ...item, enabled: !item.enabled } : item));

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-signal-400 px-4 text-sm font-semibold text-ink-950 transition hover:bg-signal-300">
          <PlusIcon className="h-4 w-4" />新建预算订阅
        </button>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        {items.map((item) => (
          <Panel key={item.id} className={`p-5 sm:p-6 ${item.enabled ? "" : "opacity-65"}`}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-lg font-semibold text-white">{item.name}</h2>
                  <StatusPill tone={item.enabled ? "teal" : "slate"}>{item.enabled ? "扫描中" : "已暂停"}</StatusPill>
                </div>
                <p className="mt-2 text-sm text-slate-500">{item.platforms.join(" + ")}</p>
              </div>
              <button
                type="button"
                onClick={() => toggle(item.id)}
                className={`relative h-7 w-12 shrink-0 rounded-full transition ${item.enabled ? "bg-signal-400" : "bg-slate-700"}`}
                aria-label={item.enabled ? `暂停${item.name}` : `启用${item.name}`}
                aria-pressed={item.enabled}
              >
                <span className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow transition ${item.enabled ? "left-6" : "left-1"}`} />
              </button>
            </div>

            <div className="mt-5 grid grid-cols-2 gap-4 border-y border-white/[.065] py-4 sm:grid-cols-4">
              <div><div className="text-xs text-slate-500">全口径上限</div><div className="mt-1 font-semibold text-white">{formatMoney(item.budget)}</div></div>
              <div><div className="text-xs text-slate-500">最低安全 ROI</div><div className="mt-1 font-semibold text-signal-300">{formatPercent(item.minSafeRoi)}</div></div>
              <div><div className="text-xs text-slate-500">未知费用</div><div className="mt-1 font-semibold text-amber-200">≤ {item.maxUnknownCosts} 项</div></div>
              <div><div className="text-xs text-slate-500">本次匹配</div><div className="mt-1 font-semibold text-white">{item.lastMatched} 项</div></div>
            </div>

            <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-400">
              <span className="inline-flex items-center gap-1.5"><MapPinIcon className="h-4 w-4 text-slate-500" />{item.region}</span>
              <span className="inline-flex items-center gap-1.5"><WrenchScrewdriverIcon className="h-4 w-4 text-slate-500" />{item.categories.join("、")}</span>
              <span className="inline-flex items-center gap-1.5"><SignalIcon className="h-4 w-4 text-slate-500" />{item.productionFirst ? "生产型优先" : "转卖型优先"}</span>
            </div>

            <div className="mt-5 flex items-center justify-between gap-3 rounded-xl bg-white/[.025] px-3.5 py-3 text-sm">
              <span className="inline-flex items-center gap-2 text-slate-400">
                {item.enabled ? <CheckCircleIcon className="h-4 w-4 text-signal-300" /> : <PauseCircleIcon className="h-4 w-4" />}
                {item.enabled ? "符合条件时生成站内提醒" : "暂停期间不扫描"}
              </span>
              <button className="font-medium text-signal-300 hover:text-signal-200">编辑</button>
            </div>
          </Panel>
        ))}
      </div>
      <div className="flex items-start gap-2 rounded-xl border border-sky-400/15 bg-sky-400/[.05] p-4 text-sm leading-6 text-sky-100/70">
        <BellAlertIcon className="mt-0.5 h-4 w-4 shrink-0 text-sky-300" />Phase 0 只演示订阅规则与模拟匹配，不发送外部通知。
      </div>
    </div>
  );
}
