export type CostStatus = "known" | "estimated" | "unknown";

export interface CostItem {
  id: string;
  feeName: string;
  minAmount: number | null;
  maxAmount: number | null;
  status: CostStatus;
  evidenceText: string;
  evidenceSource: string;
  confidence: number | null;
}

export interface Comparable {
  id: string;
  title: string;
  price: number | null;
  region: string;
  condition: string;
  status: "listing" | "sold";
  note: string;
}

export interface Opportunity {
  conservativeResaleValue: number | null;
  allInCostMin: number | null;
  allInCostMax: number | null;
  safeMargin: number | null;
  safeRoi: number | null;
  maxRecommendedBid: number | null;
  minimumCashRequired: number | null;
  capitalFitScore: number;
  liquidityScore: number;
  skillFitScore: number;
  productionScore: number;
  costCertaintyScore: number;
  distanceScore: number;
  overallScore: number;
  grade: "S" | "A" | "B" | "C" | "Skip";
  estimatedMonthlyIncome: number | null;
  paybackMonths: number | null;
  recommendedUse: string;
  unknownCostCount: number;
  costEstimateComplete: boolean;
  valuationAvailable: boolean;
}

export interface Asset {
  id: string;
  sourcePlatform: string;
  sourceMode: string;
  externalId: string;
  title: string;
  category: string;
  subcategory: string;
  province: string;
  city: string;
  district: string;
  seller: string;
  auctionStage: "一拍" | "二拍" | "变卖" | "清仓";
  status: "竞价中" | "即将开始" | "待核验" | "已结束";
  startTime: string | null;
  endTime: string | null;
  appraisalPrice: number | null;
  startPrice: number | null;
  currentPrice: number | null;
  deposit: number | null;
  bidIncrement: number | null;
  distanceKm: number;
  matchedSkills: string[];
  watchlisted?: boolean;
  changeNote?: string;
  summary: string;
  opportunity: Opportunity;
  costs: CostItem[];
  comparables: Comparable[];
  evidence: string[];
  pendingChecks: string[];
}

export interface UserProfile {
  name: string;
  city: string;
  availableCapital: number;
  livingReserve: number;
  debtRepaymentFund: number;
  monthlyNewCapital: number;
  monthlyAssetProfit: number;
  searchRadius: number;
  skills: string[];
  preferredAssetTypes: string[];
  preferredStrategy: "production" | "resale" | "hybrid";
  maxSingleExposure: number;
  storageAvailable: boolean;
  vehicleAvailable: boolean;
}

export interface Subscription {
  id: string;
  name: string;
  platforms: string[];
  region: string;
  budget: number;
  categories: string[];
  minSafeRoi: number;
  maxUnknownCosts: number;
  productionFirst: boolean;
  enabled: boolean;
  lastMatched: number;
}
