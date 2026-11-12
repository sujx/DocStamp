/**
 * sitemap 的 URL 集必须与导航单一数据源一致：
 * 首页 + 仪表盘 + 14 个非 dashboard 条目 = 16 条，顺序固定、无重复。
 * 不启服务器，只验纯函数。
 */
import { describe, it, expect } from "vitest";
import { TOOLS } from "../../../composables/tools.config";
import { buildSitemapUrls, renderSitemapXml, SITE_ORIGIN } from "../../utils/sitemap";

const PATHS = ["/", "/tools", ...TOOLS.filter((t) => t.key !== "dashboard").map((t) => t.to)];

describe("sitemap urls", () => {
  it("等于 / + /tools + 全部非 dashboard 工具路由", () => {
    const relative = buildSitemapUrls(TOOLS, "https://s.test").map((u) => u.replace("https://s.test", ""));
    expect(relative).toEqual(PATHS);
  });

  it("恰好 16 条、顺序固定、无重复", () => {
    expect(PATHS).toHaveLength(16);
    expect(new Set(PATHS).size).toBe(16);
    expect(PATHS).toContain("/pdf-redact");
    expect(PATHS.filter((p) => p === "/tools")).toHaveLength(1);
  });

  it("默认用站点正式域名，且不出现双斜杠", () => {
    const urls = buildSitemapUrls(TOOLS);
    expect(urls[0]).toBe(`${SITE_ORIGIN}/`);
    for (const url of urls) {
      expect(url).toMatch(/^https:\/\/doc\.sujx\.net\/[a-z-]*$/);
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
});
