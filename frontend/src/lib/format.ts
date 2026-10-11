export function minutes(value: number | null | undefined): string {
  if (value == null) return "—";
  const hours = Math.floor(value / 60) % 24;
  return `${String(hours).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`;
}