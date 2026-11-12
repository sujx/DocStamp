export interface SitemapEntry {
  key: string
  to: string
}

export const SITE_ORIGIN = "https://doc.sujx.net";

// 与 frontend/public/robots.txt 的 Sitemap 行同源；SSG 下没有请求头可依赖，
// 正式域名只能在这里写死。
export function buildSitemapUrls(tools: SitemapEntry[], base: string = SITE_ORIGIN): string[] {
  const paths = ["/", "/tools", ...tools.filter((t) => t.key !== "dashboard").map((t) => t.to)];
  return paths.map((path) => `${base}${path}`);
}

export function renderSitemapXml(urls: string[], lastmod: string): string {
  const body = urls
    .map((url) => `  <url><loc>${url}</loc><lastmod>${lastmod}</lastmod></url>`)
    .join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${body}
</urlset>
`;
}
