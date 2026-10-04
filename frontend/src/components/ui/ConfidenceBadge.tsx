import { mapConfidenceToPercent, confidenceVariant } from "@/lib/viewModel";

interface ConfidenceBadgeProps {
  value?: number | null;
  label?: string;
  small?: boolean;
}

const VARIANT_LABELS = { high: "Yüksek", medium: "Orta", low: "Düşük" };

export default function ConfidenceBadge({ value, label, small = false }: ConfidenceBadgeProps) {
  if (value == null || typeof value !== "number") return null;
  const variant = confidenceVariant(value);
  const pct = mapConfidenceToPercent(value);
  const variantLabel = VARIANT_LABELS[variant];
  const displayLabel = label ? `${label}: ${pct}` : pct;

  return (
    <span
      className={`ota-confidence-badge ${variant}${small ? " small" : ""}`}
      title={`Güven: ${pct} (${variantLabel})`}
      aria-label={`Güven skoru: ${pct}`}
    >
      {displayLabel}
    </span>
  );
}
