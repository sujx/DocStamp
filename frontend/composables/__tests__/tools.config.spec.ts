/**
 * Tests for the tools single source of truth.
 *
 * 侧栏自 v3.7.2 起是扁平的：没有分组子菜单，SIDEBAR_ITEMS 就是按 order 排好的
 * 工具列表。这层契约在这里钉住，避免分组概念被无意间重新引入。
 */
import { describe, it, expect } from "vitest";
import { TOOLS, SIDEBAR_ITEMS } from "../tools.config";

const PDF_KEYS = ["file-assembly", "print-split", "pdf-editor", "pdf-tools", "pdf-merge"];

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

  it("五个 PDF 工具拉平后保持原有相对顺序", () => {
    const keys = SIDEBAR_ITEMS.map((item) => item.key);
    expect(keys.filter((key) => PDF_KEYS.includes(key))).toEqual(PDF_KEYS);
  });
});
