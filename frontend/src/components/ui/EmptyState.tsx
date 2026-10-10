import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  compact?: boolean;
  premium?: boolean;
}

export default function EmptyState({ icon, title, description, action, compact = false, premium = true }: EmptyStateProps) {
  return (
    <div className={`ota-empty-state${compact ? " compact" : ""}${premium ? " premium" : ""}`}>
      {icon && <div className="ota-empty-icon" aria-hidden="true">{icon}</div>}
      <h3 className="ota-empty-title">{title}</h3>
      {description && <p className="ota-empty-desc">{description}</p>}
      {action && <div className="ota-empty-action">{action}</div>}
    </div>
  );
}
