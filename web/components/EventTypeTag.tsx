const TYPE_STYLES: Record<string, string> = {
  appointment: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300",
  scan: "bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300",
  vet: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  birthday: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  other: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
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
