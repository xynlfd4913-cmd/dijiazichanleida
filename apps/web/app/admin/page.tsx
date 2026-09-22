import {
  ArrowPathIcon,
  BeakerIcon,
  CheckCircleIcon,
  CircleStackIcon,
  ClockIcon,
  CodeBracketSquareIcon,
  ExclamationTriangleIcon,
  ServerStackIcon,
} from "@heroicons/react/24/outline";
import { DemoNotice, PageHeader, Panel, SectionHeading, StatusPill } from "@/components/ui";
import { getAdminStatus } from "@/lib/api";

export const metadata = { title: "后台" };

const sourceLabels: Record<string, string> = {
  ali_jianlou: "阿里捡漏 Adapter",
  ovupre: "湖北产权 Adapter",
  gpai: "公拍 Adapter",
  pccz: "破产资产 Adapter",
};

export default async function AdminPage() {
  const system = await getAdminStatus();
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="系统运行" title="后台" description="检查适配器、任务、原始快照与人工修正；Phase 0 所有来源均处于模拟或骨架模式。" action={<div className="flex flex-wrap items-center gap-2"><StatusPill tone={system.source === "api" ? "teal" : "amber"}>{system.source === "api" ? "本地 API 数据" : "内置模拟回退"}</StatusPill><button className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-white/10 bg-white/[.035] px-4 text-sm font-medium text-slate-200"><ArrowPathIcon className="h-4 w-4" />刷新状态</button></div>} />
      <DemoNotice />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Panel className="p-5"><div className="flex items-center justify-between"><ServerStackIcon className="h-5 w-5 text-signal-300" /><StatusPill tone="teal">{system.runtimeMode}</StatusPill></div><div className="mt-4 text-2xl font-semibold text-white">{system.sources.length}</div><p className="mt-1 text-sm text-slate-500">已登记模拟数据源</p></Panel>
        <Panel className="p-5"><div className="flex items-center justify-between"><CircleStackIcon className="h-5 w-5 text-sky-300" /><StatusPill>{system.database}</StatusPill></div><div className="mt-4 text-2xl font-semibold text-white">{system.totals.assets}</div><p className="mt-1 text-sm text-slate-500">当前资产记录</p></Panel>
        <Panel className="p-5"><div className="flex items-center justify-between"><ClockIcon className="h-5 w-5 text-amber-200" /><StatusPill tone="amber">{system.schedulerEnabled ? "已启用" : "未启用"}</StatusPill></div><div className="mt-4 text-2xl font-semibold text-amber-200">{system.totals.unknownCosts}</div><p className="mt-1 text-sm text-slate-500">未知费用项目</p></Panel>
        <Panel className="p-5"><div className="flex items-center justify-between"><BeakerIcon className="h-5 w-5 text-violet-300" /><StatusPill tone={system.networkEnabled ? "rose" : "sky"}>Phase 0</StatusPill></div><div className="mt-4 text-2xl font-semibold text-white">{system.networkEnabled ? "已开启" : "0"}</div><p className="mt-1 text-sm text-slate-500">真实网站请求</p></Panel>
      </section>

      <Panel className="overflow-hidden">
        <div className="border-b border-white/[.07] p-5 sm:p-6"><SectionHeading title="数据源与适配器" detail="真实抓取显式关闭" /></div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-white/[.065] bg-white/[.02] text-xs uppercase tracking-wider text-slate-600"><tr><th className="px-6 py-3.5 font-medium">Adapter</th><th className="px-6 py-3.5 font-medium">运行模式</th><th className="px-6 py-3.5 font-medium">本次记录</th><th className="px-6 py-3.5 font-medium">最近任务</th><th className="px-6 py-3.5 font-medium">状态</th><th className="px-6 py-3.5 font-medium">操作</th></tr></thead>
            <tbody className="divide-y divide-white/[.055]">
              {system.sources.map((source) => (
                <tr key={source.name} className="text-slate-300 hover:bg-white/[.02]">
                  <td className="px-6 py-4"><div className="font-medium text-white">{sourceLabels[source.name] ?? source.name}</div><div className="mt-1 font-mono text-xs text-slate-600">{source.name}</div></td>
                  <td className="px-6 py-4"><StatusPill>{source.mode}</StatusPill></td>
                  <td className="px-6 py-4 tabular-nums">{source.assetCount}</td>
                  <td className="px-6 py-4">{source.lastScan}</td>
                  <td className="px-6 py-4">{source.status === "seeded" || source.status === "ready" ? <span className="inline-flex items-center gap-1.5 text-signal-300"><CheckCircleIcon className="h-4 w-4" />就绪</span> : <span className="inline-flex items-center gap-1.5 text-amber-200"><ExclamationTriangleIcon className="h-4 w-4" />{source.status === "fallback" ? "内置回退" : "待检查"}</span>}</td>
                  <td className="px-6 py-4"><button className="font-medium text-signal-300 hover:text-signal-200">查看快照</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_.8fr]">
        <Panel className="p-5 sm:p-6">
          <SectionHeading title="本地运行概览" detail={system.source === "api" ? "来自 /api/admin/status" : "API 未启动，显示内置回退状态"} />
          <div className="mt-6 space-y-4">
            {[
              ["统一资产记录", system.totals.assets, "text-signal-300"],
              ["未知费用项目", system.totals.unknownCosts, "text-amber-200"],
              ["抓取错误", system.totals.crawlerErrors, system.totals.crawlerErrors ? "text-rose-300" : "text-signal-300"],
              ["结构变化提醒", system.totals.structureAlerts, system.totals.structureAlerts ? "text-amber-200" : "text-signal-300"],
            ].map(([label, value, color]) => (
              <div key={String(label)} className="flex items-center justify-between rounded-xl bg-white/[.025] px-4 py-3">
                <span className="text-sm text-slate-400">{label}</span><span className={`text-lg font-semibold ${color}`}>{value}</span>
              </div>
            ))}
            <p className="text-xs leading-5 text-slate-600">{system.schedulerReason}</p>
          </div>
        </Panel>

        <Panel className="p-5 sm:p-6">
          <SectionHeading title="需要人工处理" detail="不会被模型自动填零" />
          <div className="mt-5 space-y-3">
            <div className="flex w-full items-center justify-between rounded-xl border border-amber-300/10 bg-amber-300/[.04] p-4 text-left"><span><span className="block text-sm font-medium text-white">未知费用待补充</span><span className="mt-1 block text-xs text-slate-500">运输、维修、税费等</span></span><strong className="text-xl text-amber-200">{system.totals.unknownCosts}</strong></div>
            <div className="flex w-full items-center justify-between rounded-xl border border-white/[.07] bg-white/[.025] p-4 text-left"><span><span className="block text-sm font-medium text-white">市场参照不足</span><span className="mt-1 block text-xs text-slate-500">Phase 0 后台尚未单列统计</span></span><strong className="text-sm font-medium text-slate-400">待统计</strong></div>
            <div className="flex w-full items-center justify-between rounded-xl border border-white/[.07] bg-white/[.025] p-4 text-left"><span><span className="block text-sm font-medium text-white">字段人工修正</span><span className="mt-1 block text-xs text-slate-500">Phase 1 接入真实来源后启用</span></span><strong className="text-sm font-medium text-slate-400">未启用</strong></div>
          </div>
        </Panel>
      </section>

      <Panel className="p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3"><CodeBracketSquareIcon className="mt-0.5 h-5 w-5 text-signal-300" /><div><div className="font-medium text-white">API 模式优先，页面解析兜底</div><p className="mt-1 text-sm leading-6 text-slate-500">上层业务只读取统一资产模型，不关心数据来自 API、公开结构化数据还是后续的页面解析。</p></div></div>
          <div className="shrink-0 rounded-xl bg-white/[.035] px-4 py-3 text-right"><div className="text-xs text-slate-500">当前资产记录</div><div className="mt-1 font-semibold text-white">{system.totals.assets.toLocaleString("zh-CN")}</div></div>
        </div>
      </Panel>
    </div>
  );
}
