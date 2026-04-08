interface MetricsCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  colorClass?: string;
}

export default function MetricsCard({
  label,
  value,
  subtext,
  colorClass = "text-andromeda-700",
}: MetricsCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-1">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </p>
      <p className={`text-3xl font-bold ${colorClass}`}>{value}</p>
      {subtext && <p className="text-xs text-gray-400">{subtext}</p>}
    </div>
  );
}
