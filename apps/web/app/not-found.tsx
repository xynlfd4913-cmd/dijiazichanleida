import Link from "next/link";

export default function NotFound() {
  return (
    <div className="grid min-h-[65vh] place-items-center text-center">
      <div>
        <div className="text-sm font-semibold uppercase tracking-[.2em] text-signal-300">404</div>
        <h1 className="mt-3 text-3xl font-semibold text-white">没有找到这个模拟资产</h1>
        <p className="mt-3 text-slate-500">它可能已从演示数据中移除。</p>
        <Link href="/radar" className="mt-6 inline-flex min-h-11 items-center rounded-xl bg-signal-400 px-4 text-sm font-semibold text-ink-950">返回资产雷达</Link>
      </div>
    </div>
  );
}
