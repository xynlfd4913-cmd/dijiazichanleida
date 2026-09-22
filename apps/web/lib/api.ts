import { mockAssets, profile, scanStats, subscriptions } from "./data";
import type { Asset, Comparable, CostItem, Opportunity, Subscription, UserProfile } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
const SERVER_API_BASE_URL = process.env.API_INTERNAL_BASE_URL ?? API_BASE_URL;

type UnknownRecord = Record<string, unknown>;

function object(value: unknown): UnknownRecord {
  return value !== null && typeof value === "object" && !Array.isArray(value) ? value as UnknownRecord : {};
}

function array(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function textValue(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : value === null || value === undefined ? fallback : String(value);
}

function numberValue(value: unknown, fallback = 0): number {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function nullableNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function firstField(raw: UnknownRecord, snakeCase: string, camelCase: string): unknown {
  return raw[snakeCase] !== undefined ? raw[snakeCase] : raw[camelCase];
}

function booleanValue(value: unknown, fallback = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function stringList(value: unknown): string[] {
  return array(value).map((item) => textValue(item)).filter(Boolean);
}

async function fetchJson(path: string): Promise<unknown | null> {
  try {
    const baseUrl = typeof window === "undefined" ? SERVER_API_BASE_URL : API_BASE_URL;
    const response = await fetch(`${baseUrl}${path}`, {
      next: { revalidate: 60 },
      signal: AbortSignal.timeout(1800),
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

function normalizeCost(value: unknown, index: number): CostItem {
  const raw = object(value);
  const rawStatus = textValue(raw.status, "unknown");
  const status: CostItem["status"] = rawStatus === "known" || rawStatus === "estimated" ? rawStatus : "unknown";
  return {
    id: textValue(raw.id, `cost-${index}`),
    feeName: textValue(raw.fee_name ?? raw.feeName, "未命名费用"),
    minAmount: nullableNumber(firstField(raw, "min_amount", "minAmount")),
    maxAmount: nullableNumber(firstField(raw, "max_amount", "maxAmount")),
    status,
    evidenceText: textValue(raw.evidence_text ?? raw.evidenceText, "等待人工补充证据"),
    evidenceSource: textValue(raw.evidence_source ?? raw.evidenceSource, "本地模拟数据"),
    confidence: raw.confidence === null || raw.confidence === undefined ? null : numberValue(raw.confidence),
  };
}

function normalizeComparable(value: unknown, index: number): Comparable {
  const raw = object(value);
  const brandModel = [textValue(raw.brand), textValue(raw.model)].filter(Boolean).join(" ");
  return {
    id: textValue(raw.id, `comparable-${index}`),
    title: textValue(raw.title, brandModel || `同类市场参照 ${index + 1}`),
    price: nullableNumber(raw.price),
    region: textValue(raw.region, "地区待核验"),
    condition: textValue(raw.condition, "成色待核验"),
    status: textValue(raw.listing_or_sold ?? raw.status) === "sold" ? "sold" : "listing",
    note: textValue(raw.notes ?? raw.note, "模拟市场参照"),
  };
}

function normalizeOpportunity(value: unknown, assetRaw: UnknownRecord): Opportunity {
  const raw = object(value);
  const gradeValue = textValue(raw.grade, "C");
  const grade: Opportunity["grade"] = gradeValue === "S" || gradeValue === "A" || gradeValue === "B" || gradeValue === "Skip" ? gradeValue : "C";
  const conservativeResaleValue = nullableNumber(firstField(raw, "conservative_resale_value", "conservativeResaleValue"));
  const allInCostMin = nullableNumber(firstField(raw, "all_in_cost_min", "allInCostMin"));
  const allInCostMax = nullableNumber(firstField(raw, "all_in_cost_max", "allInCostMax"));
  const safeMargin = nullableNumber(firstField(raw, "safe_margin", "safeMargin"));
  const safeRoi = nullableNumber(firstField(raw, "safe_roi", "safeRoi"));
  const maxRecommendedBid = nullableNumber(firstField(raw, "max_recommended_bid", "maxRecommendedBid"));
  const minimumCashRequired = nullableNumber(firstField(raw, "minimum_cash_required", "minimumCashRequired"));
  const unknownCostCount = numberValue(firstField(raw, "unknown_cost_count", "unknownCostCount"));
  const completeValue = firstField(raw, "cost_estimate_complete", "costEstimateComplete");
  const costEstimateComplete = typeof completeValue === "boolean"
    ? completeValue
    : unknownCostCount === 0 && allInCostMin !== null && allInCostMax !== null;
  return {
    conservativeResaleValue,
    allInCostMin,
    allInCostMax,
    safeMargin,
    safeRoi,
    maxRecommendedBid,
    minimumCashRequired,
    capitalFitScore: numberValue(raw.capital_fit_score ?? raw.capitalFitScore),
    liquidityScore: numberValue(raw.liquidity_score ?? raw.liquidityScore),
    skillFitScore: numberValue(raw.skill_fit_score ?? raw.skillFitScore),
    productionScore: numberValue(raw.production_score ?? raw.productionScore),
    costCertaintyScore: numberValue(raw.cost_certainty_score ?? raw.costCertaintyScore),
    distanceScore: numberValue(raw.distance_score ?? raw.distanceScore),
    overallScore: numberValue(raw.overall_score ?? raw.overallScore),
    grade,
    estimatedMonthlyIncome: nullableNumber(firstField(assetRaw, "estimated_monthly_income", "estimatedMonthlyIncome")),
    paybackMonths: nullableNumber(firstField(raw, "payback_months", "paybackMonths")),
    recommendedUse: textValue(raw.recommended_use ?? raw.recommendedUse, "先完成费用与实物核验"),
    unknownCostCount,
    costEstimateComplete,
    valuationAvailable: conservativeResaleValue !== null && allInCostMax !== null && safeMargin !== null && safeRoi !== null && maxRecommendedBid !== null,
  };
}

function normalizeAsset(value: unknown): Asset {
  const raw = object(value);
  const costsRaw = array(raw.costs ?? raw.cost_items);
  const opportunityRaw = object(raw.opportunity);
  const unknownCount = numberValue(opportunityRaw.unknown_cost_count);
  const costs = costsRaw.map(normalizeCost);
  if (!costs.length && unknownCount) {
    for (let index = 0; index < unknownCount; index += 1) {
      costs.push(normalizeCost({ id: `unknown-${index}`, fee_name: "未明确费用", status: "unknown", min_amount: null, max_amount: null }, index));
    }
  }
  const notice = textValue(raw.notice_summary ?? raw.summary) || textValue(opportunityRaw.recommendation_reason, "等待人工阅读公告并完成核验。售卖方与标的信息均为模拟数据。");
  const opportunity = normalizeOpportunity(raw.opportunity, raw);
  const stageValue = textValue(raw.auction_stage ?? raw.auctionStage, "一拍").toLowerCase();
  const stageMap: Record<string, Asset["auctionStage"]> = {
    "一拍": "一拍", first: "一拍", first_auction: "一拍", "1": "一拍",
    "二拍": "二拍", second: "二拍", second_auction: "二拍", "2": "二拍",
    "变卖": "变卖", sale: "变卖", liquidation: "变卖", disposal: "变卖",
    "清仓": "清仓", clearance: "清仓",
  };
  const auctionStage = stageMap[stageValue] ?? "一拍";
  const statusValue = textValue(raw.status, "待核验").toLowerCase();
  const statusMap: Record<string, Asset["status"]> = {
    "竞价中": "竞价中", bidding: "竞价中", live: "竞价中", auctioning: "竞价中",
    "即将开始": "即将开始", preview: "即将开始", upcoming: "即将开始", pending_start: "即将开始",
    "已结束": "已结束", ended: "已结束", sold: "已结束", closed: "已结束", finished: "已结束",
    "待核验": "待核验", pending: "待核验", verification: "待核验",
  };
  const status = statusMap[statusValue] ?? "待核验";
  const categoryValue = textValue(raw.category, "其他");
  const evidence = stringList(raw.evidence);
  if (!evidence.length) evidence.push(...costs.filter((item) => item.evidenceText).slice(0, 3).map((item) => `${item.feeName}：${item.evidenceText}`));
  if (!evidence.length) evidence.push("当前为列表摘要，请打开本地种子数据核对完整字段。");
  const pendingChecks = stringList(raw.pending_checks ?? raw.pendingChecks);
  if (!pendingChecks.length) pendingChecks.push(...costs.filter((item) => item.status === "unknown").map((item) => `核实${item.feeName}的承担方与金额`));
  if (!pendingChecks.length) pendingChecks.push("现场核对数量、状态与交付条件");

  return {
    id: textValue(raw.id),
    sourcePlatform: textValue(raw.source_platform ?? raw.sourcePlatform, "模拟来源"),
    sourceMode: textValue(raw.source_mode ?? raw.sourceMode, "mock"),
    externalId: textValue(raw.external_id ?? raw.externalId, `MOCK-${textValue(raw.id)}`),
    title: textValue(raw.title, "未命名模拟资产"),
    category: categoryValue === "机械设备" ? "机器设备" : categoryValue,
    subcategory: textValue(raw.subcategory, "其他"),
    province: textValue(raw.province, "湖北"),
    city: textValue(raw.city, "武汉"),
    district: textValue(raw.district, "地区待核验"),
    seller: textValue(raw.seller_or_court ?? raw.seller, "模拟处置方"),
    auctionStage,
    status,
    startTime: textValue(raw.start_time ?? raw.startTime) || null,
    endTime: textValue(raw.end_time ?? raw.endTime) || null,
    appraisalPrice: nullableNumber(firstField(raw, "appraisal_price", "appraisalPrice")),
    startPrice: nullableNumber(firstField(raw, "start_price", "startPrice")),
    currentPrice: nullableNumber(firstField(raw, "current_price", "currentPrice")),
    deposit: nullableNumber(raw.deposit),
    bidIncrement: nullableNumber(firstField(raw, "bid_increment", "bidIncrement")),
    distanceKm: numberValue(raw.distance_km ?? raw.distanceKm),
    matchedSkills: stringList(raw.required_skills ?? raw.matchedSkills),
    watchlisted: booleanValue(raw.watchlisted),
    changeNote: textValue(raw.change_note ?? raw.changeNote) || undefined,
    summary: notice,
    opportunity,
    costs,
    comparables: array(raw.comparables).map(normalizeComparable),
    evidence,
    pendingChecks,
  };
}

function normalizeProfile(value: unknown): UserProfile {
  const raw = object(value);
  const skills = stringList(raw.skills);
  const preferredAssets = stringList(raw.preferred_asset_types ?? raw.preferredAssetTypes);
  return {
    name: textValue(raw.name, "重启者 01"),
    city: [textValue(raw.province), textValue(raw.city)].filter(Boolean).join(" · ") || profile.city,
    availableCapital: numberValue(raw.available_capital ?? raw.availableCapital, profile.availableCapital),
    livingReserve: numberValue(raw.living_reserve ?? raw.livingReserve, profile.livingReserve),
    debtRepaymentFund: numberValue(raw.debt_repayment_fund ?? raw.debtRepaymentFund, profile.debtRepaymentFund),
    monthlyNewCapital: numberValue(raw.monthly_new_capital ?? raw.monthlyNewCapital, profile.monthlyNewCapital),
    monthlyAssetProfit: numberValue(raw.monthly_asset_profit ?? raw.monthlyAssetProfit, profile.monthlyAssetProfit),
    searchRadius: numberValue(raw.search_radius ?? raw.searchRadius, profile.searchRadius),
    skills: skills.length ? skills : profile.skills,
    preferredAssetTypes: preferredAssets.length ? preferredAssets : profile.preferredAssetTypes,
    preferredStrategy: textValue(raw.preferred_strategy ?? raw.preferredStrategy, profile.preferredStrategy) as UserProfile["preferredStrategy"],
    maxSingleExposure: numberValue(raw.max_single_exposure ?? raw.maxSingleExposure, profile.maxSingleExposure),
    storageAvailable: booleanValue(raw.storage_available ?? raw.storageAvailable, profile.storageAvailable),
    vehicleAvailable: booleanValue(raw.vehicle_available ?? raw.vehicleAvailable, profile.vehicleAvailable),
  };
}

function normalizeSubscription(value: unknown): Subscription {
  const raw = object(value);
  const region = [textValue(raw.province), textValue(raw.city)].filter(Boolean).join(" · ") || textValue(raw.region, "不限地区");
  const preferredUse = textValue(raw.preferred_use);
  const platforms = stringList(raw.platforms);
  return {
    id: textValue(raw.id),
    name: textValue(raw.name, "未命名订阅"),
    platforms: platforms.length ? platforms : [textValue(raw.platform, "全部模拟平台")],
    region,
    budget: numberValue(raw.max_all_in_cost ?? raw.budget),
    categories: stringList(raw.categories),
    minSafeRoi: numberValue(raw.min_safe_roi ?? raw.minSafeRoi),
    maxUnknownCosts: numberValue(raw.max_unknown_costs ?? raw.maxUnknownCosts, 2),
    productionFirst: preferredUse ? preferredUse === "production" : booleanValue(raw.productionFirst),
    enabled: booleanValue(raw.enabled, true),
    lastMatched: numberValue(raw.last_matched ?? raw.lastMatched),
  };
}

export async function getAssets(): Promise<Asset[]> {
  const payload = await fetchJson("/assets?page_size=100");
  if (!payload) return mockAssets;
  const raw = object(payload);
  const items = Array.isArray(payload) ? payload : array(raw.items ?? raw.data);
  return items.map(normalizeAsset);
}

export async function getAsset(id: string): Promise<Asset | undefined> {
  const payload = await fetchJson(`/assets/${encodeURIComponent(id)}`);
  if (payload) return normalizeAsset(payload);
  return mockAssets.find((item) => item.id === id);
}

export async function getProfile(): Promise<UserProfile> {
  const payload = await fetchJson("/profile");
  return payload ? normalizeProfile(payload) : profile;
}

export async function getSubscriptions(): Promise<Subscription[]> {
  const payload = await fetchJson("/subscriptions");
  if (!payload) return subscriptions;
  const items = Array.isArray(payload) ? payload : array(object(payload).items ?? object(payload).data);
  return items.map(normalizeSubscription);
}

export async function getWatchlistAssets(): Promise<Asset[]> {
  const payload = await fetchJson("/watchlist");
  if (!payload) return mockAssets.filter((item) => item.watchlisted);
  const items = Array.isArray(payload) ? payload : array(object(payload).items ?? object(payload).data);
  return items.map((item) => {
    const raw = object(item);
    return { ...normalizeAsset(raw.asset ?? item), watchlisted: true };
  });
}

export interface DashboardStats {
  scanned: number;
  capitalFit: number;
  regionFit: number;
  costPassed: number;
  comparableReady: number;
  marginPassed: number;
  skillMatched: number;
  gradeAOrAbove: number;
}

export interface DashboardData {
  profile: UserProfile;
  assets: Asset[];
  stats: DashboardStats;
  source: "api" | "fallback";
}

export async function getDashboardData(): Promise<DashboardData> {
  const payload = await fetchJson("/dashboard");
  if (!payload) {
    return {
      profile,
      assets: mockAssets,
      stats: { ...scanStats, gradeAOrAbove: mockAssets.filter((item) => item.opportunity.grade === "S" || item.opportunity.grade === "A").length },
      source: "fallback",
    };
  }
  const raw = object(payload);
  const rawStats = object(raw.scan_stats ?? raw.scanStats);
  return {
    profile: normalizeProfile(raw.profile),
    assets: array(raw.today_opportunities ?? raw.assets).map(normalizeAsset),
    stats: {
      scanned: numberValue(rawStats.scanned),
      capitalFit: numberValue(rawStats.capital_fit ?? rawStats.capitalFit),
      regionFit: numberValue(rawStats.region_fit ?? rawStats.regionFit),
      costPassed: numberValue(rawStats.hidden_cost_filtered ?? rawStats.costPassed),
      comparableReady: numberValue(rawStats.with_market_reference ?? rawStats.comparableReady),
      marginPassed: numberValue(rawStats.positive_safe_margin ?? rawStats.marginPassed),
      skillMatched: numberValue(rawStats.skill_fit ?? rawStats.skillMatched),
      gradeAOrAbove: numberValue(rawStats.grade_a_or_above ?? rawStats.gradeAOrAbove),
    },
    source: "api",
  };
}

export interface AdminSourceStatus {
  name: string;
  mode: string;
  status: string;
  assetCount: number;
  lastScan: string;
}

export interface AdminStatusData {
  runtimeMode: string;
  networkEnabled: boolean;
  database: string;
  sources: AdminSourceStatus[];
  totals: { assets: number; unknownCosts: number; crawlerErrors: number; structureAlerts: number };
  schedulerEnabled: boolean;
  schedulerReason: string;
  source: "api" | "fallback";
}

export async function getAdminStatus(): Promise<AdminStatusData> {
  const payload = await fetchJson("/admin/status");
  if (!payload) {
    return {
      runtimeMode: "offline_mock",
      networkEnabled: false,
      database: "未连接 API",
      sources: [
        { name: "ali_jianlou", mode: "骨架", status: "fallback", assetCount: 2, lastScan: "未运行" },
        { name: "ovupre", mode: "内置模拟", status: "fallback", assetCount: 1, lastScan: "未运行" },
        { name: "gpai", mode: "内置模拟", status: "fallback", assetCount: 2, lastScan: "未运行" },
        { name: "pccz", mode: "内置模拟", status: "fallback", assetCount: 1, lastScan: "未运行" },
      ],
      totals: {
        assets: mockAssets.length,
        unknownCosts: mockAssets.reduce((total, asset) => total + asset.opportunity.unknownCostCount, 0),
        crawlerErrors: 0,
        structureAlerts: 0,
      },
      schedulerEnabled: false,
      schedulerReason: "API 未启动，页面正在显示内置 Phase 0 模拟状态。",
      source: "fallback",
    };
  }
  const raw = object(payload);
  const totals = object(raw.totals);
  const scheduler = object(raw.scheduler);
  return {
    runtimeMode: textValue(raw.runtime_mode ?? raw.runtimeMode, "offline_mock"),
    networkEnabled: booleanValue(raw.real_network_enabled ?? raw.networkEnabled),
    database: textValue(raw.database, "unknown"),
    sources: array(raw.sources).map((item) => {
      const source = object(item);
      return {
        name: textValue(source.name, "unknown"),
        mode: textValue(source.mode, "mock"),
        status: textValue(source.status, "unknown"),
        assetCount: numberValue(source.asset_count ?? source.assetCount),
        lastScan: textValue(source.last_scan ?? source.lastScan, "未运行"),
      };
    }),
    totals: {
      assets: numberValue(totals.assets),
      unknownCosts: numberValue(totals.unknown_cost_items ?? totals.unknownCosts),
      crawlerErrors: numberValue(totals.crawler_errors ?? totals.crawlerErrors),
      structureAlerts: numberValue(totals.structure_change_alerts ?? totals.structureAlerts),
    },
    schedulerEnabled: booleanValue(scheduler.enabled),
    schedulerReason: textValue(scheduler.reason),
    source: "api",
  };
}

export { API_BASE_URL };
