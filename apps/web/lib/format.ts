export function formatMoney(value: number | null, compact = false, missingLabel = "待核验") {
  if (value === null || !Number.isFinite(value)) return missingLabel;
  if (compact && value >= 10000) {
    return `${(value / 10000).toFixed(value % 10000 === 0 ? 0 : 1)} 万`;
  }
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPercent(value: number | null, missingLabel = "待核验") {
  if (value === null || !Number.isFinite(value)) return missingLabel;
  return `${Math.round(value * 100)}%`;
}

export function formatDateTime(value: string | null) {
  if (!value) return "时间待核验";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "时间待核验";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

export function daysUntil(value: string | null) {
  if (!value) return "时间待核验";
  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) return "时间待核验";
  const diff = timestamp - Date.now();
  if (diff <= 0) return "已结束";
  const hours = Math.ceil(diff / 3_600_000);
  if (hours < 24) return `${hours} 小时后`;
  return `${Math.ceil(hours / 24)} 天后`;
}

export function cnList(values: string[]) {
  return values.join("、");
}
