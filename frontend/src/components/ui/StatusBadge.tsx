interface StatusBadgeProps {
  variant: "success" | "warning" | "error" | "info" | "neutral";
  label: string;
  tooltip?: string;
  small?: boolean;
}

export default function StatusBadge({ variant, label, tooltip, small = false }: StatusBadgeProps) {
  return (
    <span
      className={`ota-badge ota-badge-${variant}${small ? " small" : ""}`}
      title={tooltip}
      role="status"
      aria-label={tooltip ?? label}
    >
      {label}
    </span>
  );
}
