/**
 * useInterestCalc 的纯部分：表单 → 引擎输入的映射，以及校验边界。
 * 不触发 useInterestCalc() 本身，避免依赖 Nuxt 上下文。
 */
import { describe, expect, it } from "vitest";
import {
  createDefaultForm,
  formatPercent,
  toPeriods,
  toInterestInput,
  validateForm,
  type InterestForm,
} from "../useInterestCalc";

function form(over: Partial<InterestForm> = {}): InterestForm {
  return { ...createDefaultForm(), ...over };
}

describe("表单折算", () => {
  it("期限按年/月两种单位折算成月数", () => {
    expect(toPeriods(form({ periodValue: "30", periodUnit: "year" }))).toBe(360);
    expect(toPeriods(form({ periodValue: "24", periodUnit: "month" }))).toBe(24);
    expect(toPeriods(form({ periodValue: "29.5", periodUnit: "year" }))).toBe(354);
    expect(toPeriods(form({ periodValue: "" }))).toBe(0);
    expect(toPeriods(form({ periodValue: "abc" }))).toBe(0);
  });

  it("金额与费率取不到数时按 0 处理，不让 NaN 进引擎", () => {
    const input = toInterestInput(
      form({ principal: "", upfrontFee: "abc", periodFeeRate: "" }),
    );
    expect(input.principal).toBe(0);
    expect(input.upfrontFee).toBe(0);
    expect(input.periodFeeRate).toBe(0);
  });

  it("空字段与 0 字段在引擎看来是同一件事", () => {
    expect(toInterestInput(form({ upfrontFee: "0" }))).toEqual(
      toInterestInput(form({ upfrontFee: "" })),
    );
  });

  it("UInput type=number 交来的是 number，不许把它当字符串处理而抛错", () => {
    // 历史 bug：num() 无条件 value.trim()，键入一次就 TypeError，
    // Vue 把整个期限行卸载掉，页面剩下一句「页面组件出错，请刷新重试」。
    expect(toPeriods(form({ periodValue: 24, periodUnit: "month" }))).toBe(24);
    const input = toInterestInput(form({ principal: 120000, rate: 0, periodFeeRate: 0.6 }));
    expect(input.principal).toBe(120000);
    expect(input.rate).toBe(0);
    expect(input.periodFeeRate).toBe(0.6);
    expect(validateForm(form({ principal: 120000 }))).toEqual({});
  });

  it("清空数字输入框后回到空态，不抛错也不产生 NaN", () => {
    // 浏览器里删光数字框的值是 null，不是 ""
    expect(toPeriods(form({ periodValue: null }))).toBe(0);
    const input = toInterestInput(form({ principal: null, rate: null }));
    expect(input.principal).toBe(0);
    expect(input.rate).toBe(0);
    expect(Number.isNaN(input.principal)).toBe(false);
  });
});

describe("校验边界", () => {
  it("默认表单（100 万 / 30 年 / 4.9%）是合法的", () => {
    expect(validateForm(form())).toEqual({});
  });

  it("本金缺失、为 0、为非数、超出上限都拦下", () => {
    for (const bad of ["", "0", "-1", "abc", "2000000000"]) {
      expect(validateForm(form({ principal: bad })).principal, bad).toBe(
        "interestCalc.error.principal",
      );
    }
  });

  it("期限超过 600 期拦下", () => {
    expect(validateForm(form({ periodValue: "100", periodUnit: "year" })).periodValue).toBe(
      "interestCalc.error.periods",
    );
    expect(validateForm(form({ periodValue: "0" })).periodValue).toBe(
      "interestCalc.error.periods",
    );
  });

  it("把月利率当年利率填会被年化上限拦下——这是最常见的错位", () => {
    // 4.9% 年利率合法
    expect(validateForm(form({ rate: "4.9", rateUnit: "year" })).rate).toBeUndefined();
    // 0.4% 月利率合法（年化 4.8%）
    expect(validateForm(form({ rate: "0.4", rateUnit: "month" })).rate).toBeUndefined();
    // 40% 月利率 = 年化 480%，明显错位
    expect(validateForm(form({ rate: "40", rateUnit: "month" })).rate).toBe(
      "interestCalc.error.rate",
    );
    // 日息万 15 = 年化 54.75%，仍在范围内；万 50 = 182.5%，拦下
    expect(validateForm(form({ rate: "15", rateUnit: "day" })).rate).toBeUndefined();
    expect(validateForm(form({ rate: "50", rateUnit: "day" })).rate).toBe(
      "interestCalc.error.rate",
    );
  });

  it("前置费用必须严格小于本金，否则到手现金不为正", () => {
    expect(validateForm(form({ upfrontFee: "50000" })).upfrontFee).toBeUndefined();
    expect(validateForm(form({ upfrontFee: "1000000" })).upfrontFee).toBe(
      "interestCalc.error.upfrontFee",
    );
    expect(validateForm(form({ upfrontFee: "-1" })).upfrontFee).toBe(
      "interestCalc.error.upfrontFee",
    );
  });

  it("每期费率超过 5% 拦下", () => {
    expect(validateForm(form({ periodFeeRate: "0.6" })).periodFeeRate).toBeUndefined();
    expect(validateForm(form({ periodFeeRate: "6" })).periodFeeRate).toBe(
      "interestCalc.error.feeRate",
    );
  });

  it("零利率是合法输入（无息分期 / 公积金 0 息场景）", () => {
    expect(validateForm(form({ rate: "0" })).rate).toBeUndefined();
  });
});

describe("展示格式化", () => {
  it("解不出年化时给出占位符而不是 NaN%", () => {
    expect(formatPercent(null)).toBe("—");
    expect(formatPercent(13.2656)).toBe("13.27%");
  });
});
