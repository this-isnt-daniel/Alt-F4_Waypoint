export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-LK").format(value);
}

export function pluralize(count: number, singular: string, plural = `${singular}s`): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

export function sum(values: number[]): number {
  return values.reduce((total, value) => total + value, 0);
}
