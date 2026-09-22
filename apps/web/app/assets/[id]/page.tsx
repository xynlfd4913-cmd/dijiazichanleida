import {
  ArrowLeftIcon,
  BanknotesIcon,
  CalculatorIcon,
  CheckCircleIcon,
  ClockIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  LightBulbIcon,
  LockClosedIcon,
  MapPinIcon,
  ShieldCheckIcon,
  TagIcon,
  WrenchScrewdriverIcon,
} from "@heroicons/react/24/outline";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CostStatusBadge, DemoNotice, GradeBadge, Metric, Panel, ScoreBar, ScoreDial, SectionHeading, StatusPill } from "@/components/ui";
import { getAsset, getProfile } from "@/lib/api";
import { mockAssets } from "@/lib/data";
import { daysUntil, formatDateTime, formatMoney, formatPercent } from "@/lib/format";

type PageProps = { params: Promise<{ id: string }> };

export function generateStaticParams() {
  return mockAssets.map((asset) => ({ id: asset.id }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  const asset = await getAsset(id);
  return { title: asset ? asset.title : "资产详情" };
}

export default async function AssetDetailPage({ params }: PageProps) {
  const { id } = await params;
  const [asset, user] = await Promise.all([getAsset(id), getProfile()]);
  if (!asset) notFound();

  const knownCosts = asset.costs.filter((item) => item.status === "known");
  const estimatedCosts = asset.costs.filter((item) => item.status === "estimated");
  const unknownCosts = asset.costs.filter((item) => item.status === "unknown");
  const assetBudget = Math.min(user.availableCapital, user.maxSingleExposure);
  const cashFits = asset.opportunity.minimumCashRequired !== null
    && asset.opportunity.minimumCashRequired <= assetBudget
    && asset.opportunity.capitalFitScore > 0;
  const bidSafe = asset.currentPrice !== null
    && asset.opportunity.maxRecommendedBid !== null
    && asset.currentPrice <= asset.opportunity.maxRecommendedBid;
  const valuationProvisional = !asset.opportunity.costEstimateComplete;
  const canEnterReview = cashFits && bidSafe && asset.opportunity.valuationAvailable;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/radar" className="inline-flex min-h-10 items-center gap-2 text-sm text-slate-400 transition hover:text-white">
          <ArrowLeftIcon className="h-4 w-4" />返回资产雷达
        </Link>
        <div className="mt-3 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-4xl">
            <div className="flex flex-wrap items-center gap-2">
              <GradeBadge grade={asset.opportunity.grade} />
              <StatusPill tone={asset.status === "竞价中" ? "teal" : "amber"}>{asset.status}</StatusPill>
              <StatusPill>{asset.sourcePlatform}</StatusPill>
              <span className="text-xs text-slate-500">{asset.externalId}</span>
            </div>
            <h1 className="mt-4 text-balance text-2xl font-semibold leading-tight tracking-tight text-white sm:text-3xl">{asset.title}</h1>
            <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-500">
              <span className="inline-flex items-center gap-1.5"><MapPinIcon className="h-4 w-4" />{asset.province} · {asset.city} · {asset.district} · {asset.distanceKm}km</span>
              <span className="inline-flex items-center gap-1.5"><ClockIcon className="h-4 w-4" />{formatDateTime(asset.endTime)} 截止（{daysUntil(asset.endTime)}）</span>
              <span className="inline-flex items-center gap-1.5"><TagIcon className="h-4 w-4" />{asset.category} / {asset.subcategory} / {asset.auctionStage}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="min-h-11 rounded-xl border border-white/10 bg-white/[.035] px-4 text-sm font-medium text-slate-200 transition hover:bg-white/[.07]">加入关注</button>
            <a href="#checks" className="inline-flex min-h-11 items-center rounded-xl bg-signal-400 px-4 text-sm font-semibold text-ink-950 transition hover:bg-signal-300">查看核验清单</a>
          </div>
        </div>
      </div>

      <DemoNotice />

      {valuationProvisional ? (
        <div className="flex items-start gap-2.5 rounded-xl border border-amber-300/20 bg-amber-300/[.06] px-4 py-3 text-sm leading-6 text-amber-100/85">
          <ExclamationTriangleIcon className="mt-0.5 h-4 w-4 shrink-0 text-amber-200" />
          当前仍有 {Math.max(asset.opportunity.unknownCostCount, unknownCosts.length)} 项未知费用。下方成本、价差、ROI 与最大建议价均为暂估边界，未知金额没有按 0 元计入，也不能据此直接出价。
        </div>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-4">
        <Panel className="p-5"><Metric label="当前价" value={formatMoney(asset.currentPrice)} detail={asset.currentPrice === null || asset.opportunity.maxRecommendedBid === null ? "价格或建议价待核验" : bidSafe ? "仍低于最大建议出价" : "已超过最大建议出价"} tone={bidSafe ? "neutral" : "danger"} /></Panel>
        <Panel className="p-5"><Metric label="起拍价" value={formatMoney(asset.startPrice)} detail={`每次加价 ${formatMoney(asset.bidIncrement)}`} /></Panel>
        <Panel className="p-5"><Metric label="评估价" value={formatMoney(asset.appraisalPrice)} detail="仅作参考，不能代替变现价" /></Panel>
        <Panel className="border-amber-300/15 bg-amber-300/[.045] p-5"><Metric label="保证金 · 现金门槛" value={formatMoney(asset.deposit)} detail="通常可退，但竞拍期间占用现金" tone="warning" icon={<LockClosedIcon className="h-4 w-4" />} /></Panel>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.45fr_.55fr]">
        <Panel className="overflow-hidden">
          <div className="border-b border-white/[.07] p-5 sm:p-6">
            <SectionHeading title="全口径成本" detail="不是“拍下多少钱”，而是拿到手并可用 / 可卖需要多少钱" />
          </div>
          <div className="grid gap-px bg-white/[.07] sm:grid-cols-3">
            <div className="bg-ink-900 p-5">
              <div className="text-sm text-slate-500">最低总成本</div>
              <div className="mt-2 text-2xl font-semibold tabular-nums text-white">{formatMoney(asset.opportunity.allInCostMin)}</div>
              <div className="mt-1 text-xs text-slate-500">已知项 + 预计项低值</div>
            </div>
            <div className="bg-ink-900 p-5">
              <div className="text-sm text-slate-500">最高总成本</div>
              <div className="mt-2 text-2xl font-semibold tabular-nums text-amber-200">{formatMoney(asset.opportunity.allInCostMax)}</div>
              <div className="mt-1 text-xs text-slate-500">{valuationProvisional ? "暂估边界，不含未知金额" : "用于安全价差计算"}</div>
            </div>
            <div className="bg-ink-900 p-5">
              <div className="text-sm text-slate-500">最低所需现金</div>
              <div className={`mt-2 text-2xl font-semibold tabular-nums ${cashFits ? "text-signal-300" : "text-rose-300"}`}>{formatMoney(asset.opportunity.minimumCashRequired)}</div>
              <div className="mt-1 text-xs text-slate-500">{cashFits ? `未超过单笔预算 ${formatMoney(assetBudget)}` : `未知或超过单笔预算 ${formatMoney(assetBudget)}`}</div>
            </div>
          </div>

          <div className="divide-y divide-white/[.065] px-5 sm:px-6">
            {asset.costs.map((cost) => (
              <div key={cost.id} className="grid gap-3 py-4 md:grid-cols-[minmax(150px,.65fr)_minmax(160px,.45fr)_minmax(220px,1fr)] md:items-center">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-slate-200">{cost.feeName}</span>
                  <CostStatusBadge status={cost.status} />
                </div>
                <div className={`font-semibold tabular-nums ${cost.status === "unknown" ? "text-rose-300" : cost.status === "estimated" ? "text-amber-200" : "text-slate-200"}`}>
                  {cost.status === "unknown" ? "金额未知，不按 0 元" : cost.minAmount === cost.maxAmount ? formatMoney(cost.minAmount) : `${formatMoney(cost.minAmount)} – ${formatMoney(cost.maxAmount)}`}
                </div>
                <div>
                  <p className="text-sm leading-5 text-slate-400">{cost.evidenceText}</p>
                  <p className="mt-1 text-xs text-slate-600">{cost.evidenceSource}{cost.confidence !== null ? ` · 置信度 ${formatPercent(cost.confidence)}` : ""}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="grid gap-3 border-t border-white/[.07] bg-ink-950/30 px-5 py-4 text-sm sm:grid-cols-3 sm:px-6">
            <span className="text-teal-200">已知费用 {knownCosts.length} 项</span>
            <span className="text-amber-200">预计费用 {estimatedCosts.length} 项</span>
            <span className={unknownCosts.length ? "text-rose-300" : "text-slate-500"}>未知费用 {unknownCosts.length} 项</span>
          </div>
        </Panel>

        <Panel className="overflow-hidden border-signal-400/15 bg-gradient-to-b from-signal-400/[.07] to-white/[.025]">
          <div className="border-b border-signal-400/10 p-5 sm:p-6">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[.15em] text-signal-300"><ShieldCheckIcon className="h-4 w-4" />决策护栏</div>
            <div className="mt-4 text-sm text-slate-400">{valuationProvisional ? "暂估最大建议出价" : "最大建议出价"}</div>
            <div className="mt-1 text-4xl font-semibold tracking-tight text-signal-300">{formatMoney(asset.opportunity.maxRecommendedBid, false, "暂无估值")}</div>
            <p className="mt-3 text-sm leading-6 text-slate-400">{valuationProvisional ? "需先补齐未知费用，当前数值不能作为出价依据。" : "超过此价格，目标利润与风险准备金将不足。它比评估价更重要。"}</p>
          </div>
          <div className="space-y-5 p-5 sm:p-6">
            <Metric label="保守快速变现价" value={formatMoney(asset.opportunity.conservativeResaleValue, false, "暂无估值")} detail="基于模拟同类低位参照，不由 AI 猜价" />
            <div className="border-t border-white/[.07]" />
            <Metric label={valuationProvisional ? "暂估安全价差" : "安全价差"} value={formatMoney(asset.opportunity.safeMargin, false, "暂无估值")} tone={asset.opportunity.safeMargin !== null && asset.opportunity.safeMargin > 0 ? "positive" : "danger"} detail={valuationProvisional ? "尚未扣除未知金额" : "保守变现价 − 全口径最高成本"} />
            <div className="border-t border-white/[.07]" />
            <Metric label={valuationProvisional ? "暂估安全 ROI" : "安全 ROI"} value={formatPercent(asset.opportunity.safeRoi, "暂无估值")} tone={asset.opportunity.safeRoi !== null && asset.opportunity.safeRoi >= 0.2 ? "positive" : "danger"} detail={valuationProvisional ? "尚未扣除未知金额" : "安全价差 ÷ 全口径最高成本"} />
            <div className={`rounded-xl border p-4 text-sm leading-6 ${canEnterReview ? "border-signal-400/20 bg-signal-400/[.06] text-signal-100" : "border-rose-400/20 bg-rose-400/[.06] text-rose-100"}`}>
              {canEnterReview ? "当前仍在本金与建议价范围内，但需完成全部待核验项目。" : !cashFits ? "最低所需现金未知或超过当前单笔预算，不建议参与。" : !asset.opportunity.valuationAvailable ? "缺少可用市场参照，暂不能形成出价判断。" : "当前价未知或已超过最大建议出价，不建议继续加价。"}
            </div>
          </div>
        </Panel>
      </section>

      <section className="grid gap-4 xl:grid-cols-[.72fr_1.28fr]">
        <Panel className="p-5 sm:p-6">
          <SectionHeading title="个性化评分" detail={`综合评分 ${asset.opportunity.overallScore} / 100`} />
          <div className="mt-6 flex flex-wrap items-center gap-8">
            <ScoreDial score={asset.opportunity.productionScore} label="生产价值" />
            <ScoreDial score={asset.opportunity.skillFitScore} label="技能匹配" />
          </div>
          <div className="mt-7 space-y-5">
            <ScoreBar label="本金适配" score={asset.opportunity.capitalFitScore} />
            <ScoreBar label="流动性" score={asset.opportunity.liquidityScore} tone="sky" />
            <ScoreBar label="费用确定性" score={asset.opportunity.costCertaintyScore} tone="amber" />
            <ScoreBar label="距离便利" score={asset.opportunity.distanceScore} />
          </div>
          <div className="mt-6 rounded-xl bg-white/[.035] p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-white"><LightBulbIcon className="h-4 w-4 text-amber-200" />建议用途</div>
            <p className="mt-2 text-sm leading-6 text-slate-400">{asset.opportunity.recommendedUse}</p>
            {asset.opportunity.estimatedMonthlyIncome !== null && asset.opportunity.estimatedMonthlyIncome > 0 ? <p className="mt-2 text-xs text-slate-500">预计月增收 {formatMoney(asset.opportunity.estimatedMonthlyIncome)} · 静态回本约 {asset.opportunity.paybackMonths ?? "待核验"} 个月</p> : null}
          </div>
        </Panel>

        <Panel className="overflow-hidden">
          <div className="border-b border-white/[.07] p-5 sm:p-6"><SectionHeading title="市场参照" detail="保守变现价必须有可追溯参照，不展示虚构外链" /></div>
          {asset.comparables.length ? (
            <div className="divide-y divide-white/[.065]">
              {asset.comparables.map((item) => (
                <div key={item.id} className="grid gap-3 p-5 sm:grid-cols-[1fr_auto] sm:p-6">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-medium text-slate-200">{item.title}</h3>
                      <StatusPill tone={item.status === "sold" ? "teal" : "slate"}>{item.status === "sold" ? "已成交" : "挂牌中"}</StatusPill>
                    </div>
                    <p className="mt-2 text-sm text-slate-500">{item.region} · {item.condition} · {item.note}</p>
                  </div>
                  <div className="text-xl font-semibold tabular-nums text-white">{formatMoney(item.price)}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-10 text-center text-sm text-slate-500">尚无足够市场参照，不能确认真实安全空间。</div>
          )}
        </Panel>
      </section>

      <section id="checks" className="grid scroll-mt-6 gap-4 lg:grid-cols-2">
        <Panel className="p-5 sm:p-6">
          <SectionHeading title="原始公告证据" detail="仅保留支撑费用与风险判断的关键摘录" action={<DocumentTextIcon className="h-5 w-5 text-slate-500" />} />
          <ul className="mt-5 space-y-3">
            {asset.evidence.map((item, index) => (
              <li key={item} className="flex gap-3 rounded-xl bg-white/[.025] p-3.5 text-sm leading-6 text-slate-300">
                <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-lg bg-sky-400/10 text-xs font-semibold text-sky-200">{index + 1}</span>{item}
              </li>
            ))}
          </ul>
        </Panel>

        <Panel className="border-amber-300/15 bg-amber-300/[.035] p-5 sm:p-6">
          <SectionHeading title="竞拍前待核验" detail={`${asset.pendingChecks.length} 项未完成，完成前不应付款`} action={<ExclamationTriangleIcon className="h-5 w-5 text-amber-200" />} />
          <ul className="mt-5 space-y-3">
            {asset.pendingChecks.map((item) => (
              <li key={item} className="flex gap-3 rounded-xl border border-amber-200/10 bg-ink-950/25 p-3.5 text-sm leading-6 text-slate-300">
                <span className="mt-0.5 h-5 w-5 shrink-0 rounded-md border border-amber-200/30" />{item}
              </li>
            ))}
          </ul>
          <div className="mt-5 flex items-start gap-2 rounded-xl bg-rose-400/[.06] p-3.5 text-sm leading-6 text-rose-100/80">
            <EyeIcon className="mt-0.5 h-4 w-4 shrink-0" />任何未知费用不得默认为 0；需要把证据补齐后重新计算。
          </div>
        </Panel>
      </section>

      <Panel className="p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-medium text-white"><CalculatorIcon className="h-5 w-5 text-signal-300" />结论</div>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{asset.summary}</p>
          </div>
          <div className="flex shrink-0 items-center gap-3 rounded-xl bg-white/[.035] px-4 py-3">
            {canEnterReview ? <CheckCircleIcon className="h-6 w-6 text-signal-300" /> : <ExclamationTriangleIcon className="h-6 w-6 text-rose-300" />}
            <div>
              <div className="text-xs text-slate-500">当前判断</div>
              <div className="mt-0.5 font-semibold text-white">{canEnterReview ? "可进入人工核验" : "暂不参与"}</div>
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
}
