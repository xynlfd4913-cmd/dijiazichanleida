import { ProfileForm } from "@/components/profile-form";
import { PageHeader } from "@/components/ui";
import { getProfile } from "@/lib/api";

export const metadata = { title: "设置" };

export default async function SettingsPage() {
  const user = await getProfile();
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="个性化画像" title="设置" description="先定义你真正可动用的本金、技能与处置能力，系统才知道什么叫“适合你”。" />
      <ProfileForm initialProfile={user} />
    </div>
  );
}
