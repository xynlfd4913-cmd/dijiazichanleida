import { DemoNotice, PageHeader } from "@/components/ui";
import { RadarClient } from "@/components/radar-client";
import { getAssets, getProfile } from "@/lib/api";

export const metadata = { title: "低价资产雷达" };

export default async function RadarPage() {
  const [assets, user] = await Promise.all([getAssets(), getProfile()]);
  const assetBudget = Math.min(user.availableCapital, user.maxSingleExposure);
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="机会筛选"
        title="低价资产雷达"
        description="先看全口径最高成本，再看安全价差。系统不会用“评估价折扣”替代真实费用核验。"
      />
      <DemoNotice />
      <RadarClient assets={assets} assetBudget={assetBudget} />
    </div>
  );
}
