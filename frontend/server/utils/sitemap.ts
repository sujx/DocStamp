export interface SitemapEntry {
  key: string
  to: string
}

export const SITE_ORIGIN = "https://doc.sujx.net";

/** 教程页不属于 TOOLS 导航树，单独列出；新增教程时同步这里。 */
export const GUIDE_PATHS = ["/guide/pdf-redact"];

// 与 frontend/public/robots.txt 的 Sitemap 行同源；SSG 下没有请求头可依赖，
// 正式域名只能在这里写死。
export function buildSitemapUrls(tools: SitemapEntry[], base: string = SITE_ORIGIN): string[] {
  const paths = [
    "/",
    ...tools.filter((t) => t.key === "dashboard").map((t) => t.to),
    ...tools.filter((t) => t.key !== "dashboard").map((t) => t.to),
    ...GUIDE_PATHS,
  ];
  return paths.map((path) => `${base}${path}`);
}

function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function renderSitemapXml(urls: string[], lastmod: string): string {
  const body = urls
    .map((url) => `  <url><loc>${escapeXml(url)}</loc><lastmod>${lastmod}</lastmod></url>`)
    .join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${body}
</urlset>
`;
}
