import { SubscriptionList } from "@/components/subscription-list";
import { DemoNotice, PageHeader } from "@/components/ui";
import { getSubscriptions } from "@/lib/api";

export const metadata = { title: "我的订阅" };

export default async function SubscriptionsPage() {
  const items = await getSubscriptions();
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="预算订阅" title="我的订阅" description="只提醒真正落在本金、地区、费用确定性与安全 ROI 约束内的资产。" />
      <DemoNotice />
      <SubscriptionList initialSubscriptions={items} />
    </div>
  );
}
