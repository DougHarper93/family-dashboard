const TYPE_STYLES: Record<string, string> = {
  appointment: "bg-indigo-100 text-indigo-700",
  scan: "bg-pink-100 text-pink-700",
  vet: "bg-emerald-100 text-emerald-700",
  birthday: "bg-amber-100 text-amber-700",
  other: "bg-gray-100 text-gray-600",
};

const TYPE_LABELS: Record<string, string> = {
  appointment: "Appointment",
  scan: "Scan",
  vet: "Vet",
  birthday: "Birthday",
  other: "Other",
};

export default function EventTypeTag({ type }: { type: string }) {
  const style = TYPE_STYLES[type] ?? TYPE_STYLES.other;
  const label = TYPE_LABELS[type] ?? type;
  return (
    <span className={`type-badge ${style}`}>{label}</span>
  );
}
