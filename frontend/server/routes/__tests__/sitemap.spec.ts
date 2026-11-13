/**
 * sitemap 的 URL 集必须与导航单一数据源一致：
 * 首页 + 仪表盘 + 14 个非 dashboard 条目 + 1 篇教程 = 17 条，顺序固定、无重复。
 * 不启服务器，只验纯函数。
 */
import { describe, it, expect } from "vitest";
import { TOOLS } from "../../../composables/tools.config";
import { GUIDE_PATHS, buildSitemapUrls, renderSitemapXml, SITE_ORIGIN } from "../../utils/sitemap";

const DASHBOARD = TOOLS.find((t) => t.key === "dashboard")!.to;
const PATHS = ["/", DASHBOARD, ...TOOLS.filter((t) => t.key !== "dashboard").map((t) => t.to), ...GUIDE_PATHS];

describe("sitemap urls", () => {
  it("等于 / + 仪表盘路由 + 全部非 dashboard 工具路由 + 教程路由", () => {
    const relative = buildSitemapUrls(TOOLS, "https://s.test").map((u) => u.replace("https://s.test", ""));
    expect(relative).toEqual(PATHS);
  });

  it("恰好 17 条、顺序固定、无重复", () => {
    expect(PATHS).toHaveLength(17);
    expect(new Set(PATHS).size).toBe(17);
    expect(PATHS).toContain("/pdf-redact");
    expect(PATHS).toContain("/guide/pdf-redact");
    expect(PATHS.filter((p) => p === DASHBOARD)).toHaveLength(1);
  });

  it("默认用站点正式域名，且不出现双斜杠", () => {
    const urls = buildSitemapUrls(TOOLS);
    expect(urls[0]).toBe(`${SITE_ORIGIN}/`);
    for (const url of urls) {
      expect(url).toMatch(/^https:\/\/doc\.sujx\.net\/[a-z/-]*$/);
    }
  });

  it("4 个零入链的孤儿路由不得进 sitemap", () => {
    const orphans = ["/metadata-clean", "/page-decorate", "/pdf-compress", "/pdf-to-text"];
    const urls = buildSitemapUrls(TOOLS);
    for (const orphan of orphans) {
      expect(urls, `${orphan} 不会被预渲染，不该进 sitemap`).not.toContain(`${SITE_ORIGIN}${orphan}`);
    }
  });
});

describe("sitemap xml", () => {
  it("包成合法 urlset", () => {
    const xml = renderSitemapXml(["https://doc.sujx.net/"], "2026-11-12");
    expect(xml.startsWith('<?xml version="1.0" encoding="UTF-8"?>')).toBe(true);
    expect(xml).toContain('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">');
    expect(xml).toContain("<loc>https://doc.sujx.net/</loc>");
    expect(xml).toContain("<lastmod>2026-11-12</lastmod>");
    expect(xml.trimEnd().endsWith("</urlset>")).toBe(true);
  });

  it("对 loc 里的 XML 特殊字符转义", () => {
    const xml = renderSitemapXml(["https://example.com/?a=1&b=2"], "2026-11-12");
    expect(xml).toContain("&amp;");
    expect(xml).not.toMatch(/<loc>[^<]*&(?!amp;|lt;|gt;|quot;|apos;)[^<]*<\/loc>/);
    expect(xml).not.toContain('<loc>https://example.com/?a=1&b=2</loc>');
  });
});
