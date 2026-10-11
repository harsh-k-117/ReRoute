export function scaleTime(value: number, start: number, end: number): number {
  if (end <= start) return 0;
  return ((value - start) / (end - start)) * 100;
}