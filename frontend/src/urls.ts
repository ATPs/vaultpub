export function urlPrefix(): string {
  let prefix = document.body?.getAttribute("data-url-prefix") || "/";
  if (!prefix.startsWith("/")) prefix = `/${prefix}`;
  if (!prefix.endsWith("/")) prefix += "/";
  return prefix;
}

export function withUrlPrefix(path: string): string {
  if (!path.startsWith("/") || path.startsWith("//")) return path;
  const prefix = urlPrefix();
  if (prefix === "/" || path.startsWith(prefix) || path.startsWith("/static/")) return path;
  return `${prefix.replace(/\/$/, "")}${path}`;
}

export function withoutUrlPrefix(path: string): string {
  const prefix = urlPrefix();
  if (prefix === "/" || !path.startsWith(prefix)) return path;
  return `/${path.slice(prefix.length)}`;
}
