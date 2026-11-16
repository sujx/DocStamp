/**
 * 对比表每一格都必须是可读数：历史 bug 是把 totalInterest/totalFee/totalCost
 * 传进了只认 InterestResult 的 money()，解构出 undefined 后渲染成 NaN。
 *
 * 组件里的 useI18n 是 Nuxt 自动导入，vitest 裸挂载拿不到，故 stub 成取 key 的
 * 假实现——断言因此落在键名上，与文案改动解耦。
 */
import { describe, it, expect, beforeAll, vi } from "vitest";
import { mount } from "@vue/test-utils";
import InterestMethodCompare from "../InterestMethodCompare.vue";
import { calcInterest } from "~/utils/interest";
import { METHOD_OPTIONS, type MethodComparison } from "~/composables/useInterestCalc";

const CardStub = {
  template: '<div><slot name="header" /><slot /></div>',
};

function buildComparisons(): MethodComparison[] {
  return METHOD_OPTIONS.map((option) => ({
    method: option.value,
    labelKey: option.labelKey,
    result: calcInterest({
      principal: 1_000_000,
      periods: 360,
      rate: 4.9,
      rateUnit: "year",
      method: option.value,
      periodFeeRate: 0.05,
      upfrontFee: 10_000,
    }),
  }));
}

function mountTable(currentMethod = "annuity") {
  return mount(InterestMethodCompare, {
    props: { comparisons: buildComparisons(), currentMethod },
    global: { stubs: { UCard: CardStub } },
  });
}

beforeAll(() => {
  vi.stubGlobal("useI18n", () => ({ t: (key: string) => key, locale: { value: "zh-CN" } }));
});

describe("InterestMethodCompare 单元格渲染", () => {
  it("四行 × 五列全部渲染成数字，一个 NaN 都不许出现", () => {
    expect(mountTable().text()).not.toContain("NaN");
  });

  it("利息/费用/全成本三列各自独立成格，不再共用每期区间格式", () => {
    const rows = mountTable().findAll("tbody tr");

    expect(rows).toHaveLength(4);
    for (const row of rows) {
      const cells = row.findAll("td").map((td) => td.text());
      expect(cells).toHaveLength(5);
      for (const cell of cells) expect(cell).toMatch(/[\d.,]+/);
      // 每期列是「首期 → 末期」区间，其余金额列必须是单值，APR 列必须带百分号
      expect(cells[0]).toContain("→");
      expect(cells[1]).not.toContain("→");
      expect(cells[4]).toMatch(/%$/);
    }
  });

  it("只有当前方式行带「当前」标记", () => {
    const rows = mountTable("linear").findAll("tbody tr");
    const marked = rows.filter((row) => row.text().includes("interestCalc.compare.current"));

    expect(marked).toHaveLength(1);
    expect(marked[0]!.text()).toContain("interestCalc.method.linear");
  });
});
