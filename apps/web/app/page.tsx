import {
  ArrowRightIcon,
  BanknotesIcon,
  CheckBadgeIcon,
  LockClosedIcon,
  MapPinIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { AssetCard } from "@/components/asset-card";
import { DemoNotice, Metric, PageHeader, Panel, SectionHeading, Trend } from "@/components/ui";
import { getDashboardData } from "@/lib/api";
import { capitalLevels } from "@/lib/data";
import { formatMoney } from "@/lib/format";

export default async function DashboardPage() {
  const dashboard = await getDashboardData();
  const { profile: user, assets, stats: scanStats } = dashboard;
  const currentLevelIndex = capitalLevels.findLastIndex((level) => user.availableCapital >= level.threshold);
  const currentLevel = capitalLevels[Math.max(0, currentLevelIndex)];
  const nextLevel = capitalLevels[Math.min(capitalLevels.length - 1, currentLevelIndex + 1)];
  const targetProgress = currentLevel === nextLevel ? 100 : Math.round((user.availableCapital / nextLevel.threshold) * 100);
  const candidates = assets
    .filter((asset) => asset.opportunity.capitalFitScore > 0 && asset.opportunity.grade !== "Skip")
    .sort((a, b) => b.opportunity.overallScore - a.opportunity.overallScore)
    .slice(0, 2);

  return (
    <div className="space-y-6 lg:space-y-8">
      <PageHeader
        eyebrow="我的重启进度"
        title={`上午好，${user.name}`}
        description="先守住生活，再用可承受的本金寻找能生产、能变现的真实折价资产。"
        action={
          <div className="flex flex-col items-start gap-2 md:items-end">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <MapPinIcon className="h-4 w-4 text-signal-400" />
              {user.city} · {user.searchRadius} 公里
            </div>
            <span className={`rounded-md px-2 py-1 text-xs ring-1 ring-inset ${dashboard.source === "api" ? "bg-signal-400/10 text-signal-200 ring-signal-300/20" : "bg-amber-400/10 text-amber-200 ring-amber-300/20"}`}>
              {dashboard.source === "api" ? "数据源：本地 API" : "数据源：内置模拟回退"}
            </span>
          </div>
        }
      />

      <DemoNotice />

      <section className="grid gap-4 xl:grid-cols-[1.35fr_.65fr]">
        <Panel className="relative overflow-hidden p-5 sm:p-6">
          <div className="absolute -right-24 -top-24 h-64 w-64 rounded-full border border-signal-400/10" />
          <div className="absolute -right-12 -top-12 h-44 w-44 rounded-full border border-signal-400/10" />
          <div className="relative grid gap-6 md:grid-cols-[1fr_auto] md:items-center">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-signal-400/10 px-2.5 py-1 text-sm font-semibold text-signal-300 ring-1 ring-inset ring-signal-300/20">{currentLevel.level} · {currentLevel.title}</span>
                <span className="text-sm text-slate-500">当前可用资产本金</span>
              </div>
              <div className="mt-4 flex items-end gap-3">
                <span className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">{formatMoney(user.availableCapital)}</span>
                <Trend direction="up">本月 +{formatMoney(user.monthlyNewCapital)}</Trend>
              </div>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-400">这是雷达唯一允许计入购买预算的账户。单笔暴露上限 {formatMoney(user.maxSingleExposure)}。</p>
            </div>

            <div className="grid min-w-[220px] grid-cols-2 gap-3 md:grid-cols-1">
              <div className="rounded-xl border border-slate-400/10 bg-ink-950/45 px-4 py-3">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-500"><LockClosedIcon className="h-4 w-4" />生活保障账户</div>
                <div className="mt-1.5 text-lg font-semibold text-slate-200">{formatMoney(user.livingReserve)}</div>
                <div className="mt-1 text-xs text-rose-300/80">禁止用于购买资产</div>
              </div>
              <div className="rounded-xl border border-signal-400/10 bg-signal-400/[.045] px-4 py-3">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-500"><ShieldCheckIcon className="h-4 w-4" />化债账户</div>
                <div className="mt-1.5 text-lg font-semibold text-signal-200">{formatMoney(user.debtRepaymentFund)}</div>
                <div className="mt-1 text-xs text-slate-500">只记录，不自动支付</div>
              </div>
            </div>
          </div>

          <div className="relative mt-6 border-t border-white/[.065] pt-5">
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="text-slate-400">距离 {nextLevel.level} · {nextLevel.title}</span>
              <span className="font-semibold text-white">还差 {formatMoney(Math.max(nextLevel.threshold - user.availableCapital, 0))}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-white/[.06]">
              <div className="h-full rounded-full bg-gradient-to-r from-signal-500 to-sky-300" style={{ width: `${Math.min(targetProgress, 100)}%` }} />
            </div>
            <div className="mt-2 flex justify-between text-xs text-slate-600"><span>{currentLevel.level}</span><span>{targetProgress}%</span><span>{nextLevel.level}</span></div>
          </div>
        </Panel>

        <Panel className="relative flex min-h-[300px] items-center justify-center overflow-hidden p-5">
          <div className="relative h-56 w-56">
            <div className="absolute inset-0 rounded-full border border-signal-400/20" />
            <div className="absolute inset-7 rounded-full border border-signal-400/15" />
            <div className="absolute inset-14 rounded-full border border-signal-400/10" />
            <div className="radar-sweep absolute inset-0 rounded-full" />
            <div className="absolute inset-y-0 left-1/2 w-px bg-signal-400/10" />
            <div className="absolute inset-x-0 top-1/2 h-px bg-signal-400/10" />
            <span className="absolute left-[28%] top-[22%] h-2 w-2 rounded-full bg-amber-300 shadow-[0_0_12px_rgba(252,211,77,.9)]" />
            <span className="absolute bottom-[30%] right-[20%] h-2.5 w-2.5 rounded-full bg-signal-300 shadow-[0_0_16px_rgba(94,234,212,.9)]" />
            <div className="absolute inset-0 grid place-items-center text-center">
              <div className="rounded-2xl border border-white/10 bg-ink-900/90 px-5 py-3 backdrop-blur">
                <div className="text-3xl font-semibold text-white">{scanStats.scanned.toLocaleString("zh-CN")}</div>
                <div className="mt-1 text-xs text-slate-400">今日模拟扫描</div>
              </div>
            </div>
          </div>
          <div className="absolute bottom-5 left-5 right-5 flex justify-between text-xs text-slate-500">
            <span>{scanStats.capitalFit} 项本金匹配</span>
            <span className="text-signal-300">{scanStats.skillMatched} 项值得核验</span>
          </div>
        </Panel>
      </section>

      <section>
        <SectionHeading title="今日筛选漏斗" detail="保留理由比候选数量更重要" />
        <Panel className="mt-4 p-5 sm:p-6">
          <div className="grid gap-5 sm:grid-cols-3 xl:grid-cols-7">
            {[
              ["扫描", scanStats.scanned, "text-slate-200"],
              ["本金符合", scanStats.capitalFit, "text-slate-200"],
              ["地区符合", scanStats.regionFit, "text-slate-200"],
              ["费用通过", scanStats.costPassed, "text-amber-200"],
              ["有市场参照", scanStats.comparableReady, "text-sky-200"],
              ["价差合格", scanStats.marginPassed, "text-signal-200"],
              ["技能匹配", scanStats.skillMatched, "text-signal-300"],
            ].map(([label, value, color], index) => (
              <div key={String(label)} className="relative">
                <div className="text-xs text-slate-500">0{index + 1} · {label}</div>
                <div className={`mt-1.5 text-2xl font-semibold tabular-nums ${color}`}>{Number(value).toLocaleString("zh-CN")}</div>
                {index < 6 ? <ArrowRightIcon className="absolute -right-4 top-6 hidden h-4 w-4 text-slate-700 xl:block" /> : null}
              </div>
            ))}
          </div>
        </Panel>
      </section>

      <section>
        <SectionHeading
          title="最值得人工核验"
          detail="按当前分数排序；带未知费用的 B 级资产只能进入人工核验，不能直接出价"
          action={<Link href="/radar" className="inline-flex items-center gap-1.5 text-sm font-medium text-signal-300 hover:text-signal-200">查看全部 <ArrowRightIcon className="h-4 w-4" /></Link>}
        />
        <div className="mt-4 grid gap-4 2xl:grid-cols-2">
          {candidates.map((asset) => <AssetCard key={asset.id} asset={asset} />)}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Panel className="p-5"><Metric label="本月新增本金" value={formatMoney(user.monthlyNewCapital)} detail="来自主动储蓄，不含生活保障金" icon={<BanknotesIcon className="h-4 w-4" />} /></Panel>
        <Panel className="p-5"><Metric label="本月资产利润" value={formatMoney(user.monthlyAssetProfit)} tone="positive" detail="计划按 50% 补充本金、50% 进入化债账户" icon={<SparklesIcon className="h-4 w-4" />} /></Panel>
        <Panel className="p-5"><Metric label="当前技能匹配" value={`${user.skills.length} 项`} detail={user.skills.join(" · ")} icon={<CheckBadgeIcon className="h-4 w-4" />} /></Panel>
      </section>
    </div>
  );
}
