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
  colorClass = "text-andromeda-400",
}: Readonly<MetricsCardProps>) {
  return (
    <div
      className="rounded-xl p-5 space-y-1"
      style={{
        background: "rgba(255,255,255,0.05)",
        border: "1px solid rgba(255,255,255,0.08)",
        backdropFilter: "blur(12px)",
      }}
    >
      <p
        className="text-xs font-medium uppercase tracking-wide"
        style={{ color: "rgba(255,255,255,0.45)" }}
      >
        {label}
      </p>
      <p className={`text-3xl font-bold ${colorClass}`}>{value}</p>
      {subtext && (
        <p className="text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>
          {subtext}
        </p>
      )}
    </div>
  );
}
