import {
  ArrowRightIcon,
  BanknotesIcon,
  CheckCircleIcon,
  LockClosedIcon,
  ShieldCheckIcon,
} from "@heroicons/react/24/outline";
import { PageHeader, Panel, SectionHeading, StatusPill } from "@/components/ui";
import { getProfile } from "@/lib/api";
import { capitalLevels } from "@/lib/data";
import { formatMoney } from "@/lib/format";

export const metadata = { title: "资本阶梯" };

export default async function CapitalPage() {
  const user = await getProfile();
  const currentIndex = capitalLevels.findLastIndex((level) => user.availableCapital >= level.threshold);
  const next = capitalLevels[Math.min(currentIndex + 1, capitalLevels.length - 1)];
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="本金升级路径" title="资本阶梯" description="每一档只看自己承担得起的资产；升级靠储蓄与真实利润，不靠挪用生活费。" />

      <section className="grid gap-4 lg:grid-cols-3">
        <Panel className="border-signal-400/15 bg-signal-400/[.05] p-5 sm:p-6">
          <div className="flex items-center gap-2 text-sm text-slate-400"><BanknotesIcon className="h-4 w-4" />资产本金</div>
          <div className="mt-3 text-3xl font-semibold text-signal-300">{formatMoney(user.availableCapital)}</div>
          <p className="mt-2 text-sm text-slate-500">唯一可用于资产交易的预算</p>
        </Panel>
        <Panel className="p-5 sm:p-6">
          <div className="flex items-center gap-2 text-sm text-slate-400"><LockClosedIcon className="h-4 w-4" />生活保障金</div>
          <div className="mt-3 text-3xl font-semibold text-slate-200">{formatMoney(user.livingReserve)}</div>
          <p className="mt-2 text-sm text-rose-300">受保护，不参与任何资产购买</p>
        </Panel>
        <Panel className="p-5 sm:p-6">
          <div className="flex items-center gap-2 text-sm text-slate-400"><ShieldCheckIcon className="h-4 w-4" />化债账户</div>
          <div className="mt-3 text-3xl font-semibold text-white">{formatMoney(user.debtRepaymentFund)}</div>
          <p className="mt-2 text-sm text-slate-500">用于协商、结清或分期安排</p>
        </Panel>
      </section>

      <Panel className="p-5 sm:p-6">
        <SectionHeading title="从 L0 到 L6" detail={`你当前位于 ${capitalLevels[currentIndex]?.level ?? "L0"}，距离 ${next.level} 还差 ${formatMoney(Math.max(next.threshold - user.availableCapital, 0))}`} />
        <div className="mt-7 space-y-3">
          {capitalLevels.map((level, index) => {
            const reached = user.availableCapital >= level.threshold;
            const current = index === currentIndex;
            return (
              <div key={level.level} className={`grid gap-4 rounded-2xl border p-4 transition sm:grid-cols-[100px_150px_1fr_auto] sm:items-center sm:px-5 ${current ? "border-signal-400/30 bg-signal-400/[.07]" : reached ? "border-white/[.07] bg-white/[.025]" : "border-white/[.05] bg-transparent"}`}>
                <div className="flex items-center gap-3">
                  <span className={`grid h-9 w-9 place-items-center rounded-xl text-sm font-bold ${reached ? "bg-signal-400 text-ink-950" : "bg-white/[.05] text-slate-500"}`}>{level.level}</span>
                  {reached ? <CheckCircleIcon className="h-4 w-4 text-signal-300" /> : null}
                </div>
                <div>
                  <div className="font-semibold text-white">{formatMoney(level.threshold, true)}+</div>
                  <div className="mt-0.5 text-sm text-slate-500">{level.title}</div>
                </div>
                <p className="text-sm leading-6 text-slate-400">{level.focus}</p>
                {current ? <StatusPill tone="teal">当前等级</StatusPill> : reached ? <StatusPill>已达成</StatusPill> : <ArrowRightIcon className="hidden h-4 w-4 text-slate-700 sm:block" />}
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel className="overflow-hidden">
        <div className="border-b border-white/[.07] p-5 sm:p-6"><SectionHeading title="本月利润分配" detail="示例规则，可在设置中调整" /></div>
        <div className="grid gap-px bg-white/[.07] sm:grid-cols-3">
          <div className="bg-ink-900 p-5"><div className="text-sm text-slate-500">资产利润</div><div className="mt-2 text-2xl font-semibold text-white">{formatMoney(user.monthlyAssetProfit)}</div></div>
          <div className="bg-ink-900 p-5"><div className="text-sm text-slate-500">补充本金 · 50%</div><div className="mt-2 text-2xl font-semibold text-signal-300">{formatMoney(user.monthlyAssetProfit * 0.5)}</div></div>
          <div className="bg-ink-900 p-5"><div className="text-sm text-slate-500">进入化债 · 50%</div><div className="mt-2 text-2xl font-semibold text-sky-200">{formatMoney(user.monthlyAssetProfit * 0.5)}</div></div>
        </div>
      </Panel>
    </div>
  );
}
