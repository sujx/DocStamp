/**
 * Tests for the tools single source of truth.
 *
 * 侧栏自 v3.7.2 起是扁平的：没有分组子菜单，SIDEBAR_ITEMS 就是按 order 排好的
 * 工具列表。这层契约在这里钉住，避免分组概念被无意间重新引入。
 */
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { TOOLS, SIDEBAR_ITEMS, FOOTER_TOOL_KEYS, LANDING_GROUPS, LANDING_FLAGS } from "../tools.config";

const PDF_KEYS = ["file-assembly", "print-split", "pdf-editor", "pdf-tools", "pdf-merge", "pdf-redact"];

// 宣传页上写着件数的两处文案（区块标题 + 资源区一句话）。
const COUNT_KEYS = ["landing.tools.title", "landing.resource.toolsDesc"];

function readLocaleCounts(locale: string): [string, string][] {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
  const dict = JSON.parse(fs.readFileSync(path.join(root, "i18n/locales", `${locale}.json`), "utf8"));
  return COUNT_KEYS.map((key) => {
    const value = key.split(".").reduce((node: any, part) => node?.[part], dict);
    expect(typeof value, `${locale} 缺文案键 ${key}`).toBe("string");
    return [key, value as string];
  });
}

describe("tools.config", () => {
  it("侧栏条目是扁平的工具列表，不含分组对象", () => {
    expect(SIDEBAR_ITEMS).toHaveLength(TOOLS.length);
    for (const item of SIDEBAR_ITEMS) {
      expect(item).not.toHaveProperty("tools");
      expect(typeof item.to).toBe("string");
    }
  });

  it("侧栏条目按 order 升序", () => {
    const orders = SIDEBAR_ITEMS.map((item) => item.order);
    expect(orders).toEqual([...orders].sort((a, b) => a - b));
  });

  it("六个 PDF 工具拉平后保持原有相对顺序", () => {
    const keys = SIDEBAR_ITEMS.map((item) => item.key);
    expect(keys.filter((key) => PDF_KEYS.includes(key))).toEqual(PDF_KEYS);
  });

  it("没有任何导航条目占用站点根路径（/ 属于宣传页）", () => {
    for (const item of TOOLS) {
      expect(item.to, `${item.key} 不应指向 / —— / 是宣传页`).not.toBe("/");
    }
    expect(TOOLS.find((t) => t.key === "dashboard")!.to).toBe("/tools");
  });

  it("页脚精选的五件工具都能在 TOOLS 里找到", () => {
    for (const key of FOOTER_TOOL_KEYS) {
      expect(TOOLS.some((t) => t.key === key), `页脚键 ${key} 不在 TOOLS 里`).toBe(true);
    }
  });

  it("宣传页五段覆盖除仪表盘外的每一件工具，恰好一次，且都有 desc", () => {
    const keys = LANDING_GROUPS.flatMap((group) => group.keys);
    expect(keys.length, "分组里有重复键").toBe(new Set(keys).size);
    expect([...keys].sort()).toEqual(
      TOOLS.filter((t) => t.key !== "dashboard").map((t) => t.key).sort(),
    );
    for (const key of keys) {
      expect(TOOLS.find((t) => t.key === key)?.desc, `${key} 缺 desc，卡片正文会空`).toBeTruthy();
    }
  });

  it("徽章只挂在宣传页真的展示了的工具上", () => {
    const shown = new Set(LANDING_GROUPS.flatMap((group) => group.keys));
    for (const key of Object.keys(LANDING_FLAGS)) {
      expect(shown.has(key), `徽章键 ${key} 不在宣传页展示的工具里`).toBe(true);
    }
  });

  it("宣传页标题里的件数就是网格里的卡片数", () => {
    // 文案对不上网格是一句对用户撒过的谎，而卡片数来自 TOOLS，改一处不会提醒另一处。
    // 新增工具时补一行数字词，让这条测试替你想起文案。
    const words: Record<string, number> = {
      十三: 13, 十四: 14, 十五: 15, 十六: 16, 十七: 17, 十八: 18, 十九: 19, 二十: 20,
      thirteen: 13, fourteen: 14, fifteen: 15, sixteen: 16, seventeen: 17,
      eighteen: 18, nineteen: 19, twenty: 20,
    };
    const cards = LANDING_GROUPS.flatMap((group) => group.keys).length;
    for (const locale of ["zh-CN", "en"]) {
      const texts = readLocaleCounts(locale);
      for (const [key, text] of texts) {
        const lowered = text.toLowerCase();
        const claimed = Object.entries(words).find(([word]) => lowered.includes(word))?.[1];
        expect(claimed, `${locale} 的 ${key}「${text}」没写件数，或件数词不在表里`).toBe(cards);
      }
    }
  });
});
