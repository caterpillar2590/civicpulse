interface Props {
  label: string;
  tone?: "high" | "normal" | "low" | "open" | "in_progress" | "resolved" | "rejected" | "default";
}

export function Badge({ label, tone = "default" }: Props) {
  return <span className={`badge badge-${tone}`}>{label}</span>;
}
