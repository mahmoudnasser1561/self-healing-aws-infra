interface FormatOptions {
  locale?: string;
  timeZone?: string;
}

export function formatDate(iso: string, { locale, timeZone }: FormatOptions = {}) {
  return new Date(iso).toLocaleString(locale, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone,
  });
}
