/**
 * 利息引擎的数值契约。
 *
 * 锚点分两类，避免「用自身公式验自身」：
 * - 独立可证的恒等式：Σ本期还本 = 本金、末期余额 = 0、全成本 = 总利息 + 总费用，
 *   以及把求得的期利率回代 NPV 必须归零（求解器的自证）。
 * - 外部基准：先息后本与等额本息在无费用时真实年化必须回到名义报价；
 *   信用卡分期「月费率 0.6% × 24 期」的真实年化落在业内公认的 13% 附近，
 *   而不是名义上写着的 7.2%。
 */
import { describe, expect, it } from "vitest";
import {
  annualizeEarPercent,
  aprPercent,
  calcInterest,
  npv,
  toMonthlyRate,
  toNominalAnnualPercent,
  type InterestInput,
  type RepayMethod,
} from "../interest";

const P = 120_000;

function input(over: Partial<InterestInput> = {}): InterestInput {
  return {
    principal: P,
    periods: 24,
    rate: 4.9,
    rateUnit: "year",
    upfrontFee: 0,
    periodFeeRate: 0,
    method: "annuity",
    ...over,
  };
}

const METHODS: RepayMethod[] = ["annuity", "linear", "interest-first", "bullet"];

describe("利率单位换算", () => {
  it("年/月/日三种单位各自换算成月利率", () => {
    expect(toMonthlyRate(4.9, "year")).toBeCloseTo(0.049 / 12, 12);
    expect(toMonthlyRate(0.6, "month")).toBeCloseTo(0.006, 12);
    // 日息按 365 天计息年，与「日息万 2 = 年化 7.3%」的通行报价口径一致
    expect(toMonthlyRate(1.5, "day")).toBeCloseTo((1.5 / 10_000) * (365 / 12), 12);
  });

  it("名义年化百分数", () => {
    expect(toNominalAnnualPercent(4.9, "year")).toBeCloseTo(4.9, 12);
    expect(toNominalAnnualPercent(0.6, "month")).toBeCloseTo(7.2, 12);
    expect(toNominalAnnualPercent(1.5, "day")).toBeCloseTo(5.475, 12);
  });

  it("同一笔钱：月利率单位与年利率单位换进去结果相同", () => {
    const byYear = calcInterest(input({ rate: 4.9, rateUnit: "year" }));
    const byMonth = calcInterest(input({ rate: 4.9 / 12, rateUnit: "month" }));
    expect(byMonth.rows).toEqual(byYear.rows);
  });
});

describe("逐期计划表的结构恒等式", () => {
  it.each(METHODS)("%s：240 期长跑后本金闭合、余额归零", (method) => {
    const r = calcInterest(input({ method, periods: 240, rate: 4.9 }));

    expect(r.rows).toHaveLength(240);
    expect(r.rows.map((row) => row.period)).toEqual(
      Array.from({ length: 240 }, (_, i) => i + 1),
    );
    // 末期余额恰为 0，不留下 0.03 这种尾差
    expect(r.rows[239].balance).toBe(0);
    expect(r.totalPrincipal).toBeCloseTo(P, 6);
    // 每行自身也要自洽
    for (const row of r.rows) {
      expect(row.payment).toBeCloseTo(row.principalPart + row.interestPart, 6);
      expect(row.outflow).toBeCloseTo(row.payment + row.feePart, 6);
    }
  });

  it.each(METHODS)("%s：分期费用按名义本金收，不随余额衰减", (method) => {
    const r = calcInterest(input({ method, periods: 24, periodFeeRate: 0.6 }));
    const expected = Math.round(P * 0.006 * 100) / 100;
    for (const row of r.rows) expect(row.feePart).toBe(expected);
    expect(r.totalPeriodFee).toBeCloseTo(expected * 24, 6);
  });

  it("等额本息：利率为 0 时退化成均分本金，不生造利息", () => {
    const r = calcInterest(input({ rate: 0, periods: 12 }));
    expect(r.rows[0].payment).toBeCloseTo(P / 12, 6);
    expect(r.totalInterest).toBeCloseTo(0, 6);
  });

  it("等额本息：每期本息和固定", () => {
    const r = calcInterest(input({ periods: 240 }));
    const first = Math.round(r.rows[0].payment * 100);
    // 末期补差是刻意行为，其余各期必须一模一样
    for (const row of r.rows.slice(0, -1)) {
      expect(Math.round(row.payment * 100)).toBe(first);
    }
  });

  it("先息后本：中途只付息不还本，末期一次归本", () => {
    const r = calcInterest(input({ method: "interest-first", periods: 12, rate: 4.8 }));
    // 4.8%/12 = 0.4%，120000 × 0.4% = 480.00 整，无舍入噪声
    for (const row of r.rows.slice(0, -1)) {
      expect(row.principalPart).toBe(0);
      expect(row.interestPart).toBe(480);
    }
    const last = r.rows[11];
    expect(last.principalPart).toBe(P);
    expect(last.interestPart).toBe(480);
    expect(last.outflow).toBe(P + 480);
  });

  it("到期一次还本付息：中途零支出，末期本金加单利", () => {
    const r = calcInterest({
      principal: 100_000,
      periods: 12,
      rate: 0.5,
      rateUnit: "month",
      upfrontFee: 0,
      periodFeeRate: 0,
      method: "bullet",
    });
    for (const row of r.rows.slice(0, -1)) {
      expect(row.outflow).toBe(0);
      expect(row.balance).toBe(100_000);
    }
    // 单利：100000 × 0.5% × 12 = 6000
    expect(r.totalInterest).toBeCloseTo(6_000, 6);
    expect(r.rows[11].outflow).toBeCloseTo(106_000, 6);
  });

  it("等额本金：每期还本等额，利息随余额递减", () => {
    const r = calcInterest(input({ method: "linear", periods: 12, rate: 4.8 }));
    expect(r.rows[0].principalPart).toBe(P / 12);
    expect(r.rows[0].interestPart).toBe(480);
    expect(r.rows[1].interestPart).toBeLessThan(r.rows[0].interestPart);
    expect(r.firstPayment).toBeGreaterThan(r.lastPayment);
  });
});

describe("全成本口径", () => {
  it("总利息 + 总费用 = 全成本，且费用分两段计", () => {
    const r = calcInterest(input({ periods: 24, periodFeeRate: 0.6, upfrontFee: 3_600 }));
    expect(r.totalFee).toBeCloseTo(r.totalPeriodFee + r.totalUpfrontFee, 6);
    expect(r.totalCost).toBeCloseTo(r.totalInterest + r.totalFee, 6);
    // 全成本 = 各期流出合计 − 到手现金
    const sumOut = r.rows.reduce((acc, row) => acc + row.outflow, 0);
    expect(r.totalCost).toBeCloseTo(sumOut - r.disbursed, 6);
  });

  it("前置费用只减到手现金，还款基数仍按名义本金", () => {
    const r = calcInterest(input({ upfrontFee: 3_600 }));
    expect(r.disbursed).toBeCloseTo(P - 3_600, 6);
    expect(r.totalPrincipal).toBeCloseTo(P, 6);
  });

  it("无息无费时全成本为 0", () => {
    const r = calcInterest(input({ rate: 0, periods: 12 }));
    expect(r.totalCost).toBeCloseTo(0, 6);
  });
});

describe("真实年化（IRR）", () => {
  it("求得的月利率回代 NPV 必须归零——求解器的自证", () => {
    for (const method of METHODS) {
      const r = calcInterest(input({ method, periodFeeRate: 0.6, upfrontFee: 3_600 }));
      const outflows = r.rows.map((row) => row.outflow);
      expect(r.effectiveMonthlyRate).not.toBeNull();
      expect(npv(r.effectiveMonthlyRate!, r.disbursed, outflows)).toBeCloseTo(0, 1);
    }
  });

  it("先息后本无费用：真实年化回到名义报价", () => {
    const r = calcInterest(input({ method: "interest-first", periods: 12, rate: 4.8 }));
    expect(aprPercent(r.effectiveMonthlyRate!)).toBeCloseTo(4.8, 6);
  });

  it("等额本息无费用：真实年化回到名义报价", () => {
    const r = calcInterest(input({ periods: 240, rate: 4.9 }));
    expect(aprPercent(r.effectiveMonthlyRate!)).toBeCloseTo(4.9, 2);
  });

  it("到期一次还本付息（单利 6%）：EAR 恰为 6%，APR 低于报价", () => {
    const r = calcInterest({
      principal: 100_000,
      periods: 12,
      rate: 0.5,
      rateUnit: "month",
      upfrontFee: 0,
      periodFeeRate: 0,
      method: "bullet",
    });
    expect(annualizeEarPercent(r.effectiveMonthlyRate!)).toBeCloseTo(6, 3);
    expect(aprPercent(r.effectiveMonthlyRate!)).toBeLessThan(6);
  });

  it("信用卡分期：月费率 0.6% × 24 期，利率 0，真实年化 ≈ 13.3%（名义只写着 7.2%）", () => {
    const r = calcInterest(input({ method: "linear", rate: 0, periodFeeRate: 0.6 }));
    expect(r.totalInterest).toBeCloseTo(0, 6);
    expect(r.totalCost).toBeCloseTo(17_280, 6);
    // 手算独立校验：5720 × AF(24, r) = 120000 → AF = 20.979 → r ≈ 0.01105 → ×12 = 13.26%
    expect(aprPercent(r.effectiveMonthlyRate!)).toBeCloseTo(13.27, 1);
    // 表面报价 0.6% × 12 = 7.2%，真实成本接近它的两倍
    expect(r.aprPercent!).toBeGreaterThan(7.2 * 1.8);
    // 业内常引的 13% 是 APR 口径；EAR 更高，两个数都要能给出去
    expect(annualizeEarPercent(r.effectiveMonthlyRate!)).toBeGreaterThan(14);
  });

  it("同一笔分期，前置费用一多真实年化必然上抬", () => {
    const clean = calcInterest(input({ method: "linear", rate: 0, periodFeeRate: 0.6 }));
    const withFee = calcInterest(
      input({ method: "linear", rate: 0, periodFeeRate: 0.6, upfrontFee: 3_600 }),
    );
    expect(withFee.disbursed).toBeLessThan(clean.disbursed);
    expect(withFee.aprPercent).toBeGreaterThan(clean.aprPercent);
  });

  it("等额本息加费率：两种费用模型叠加后真实年化高于纯利率", () => {
    const pure = calcInterest(input({ periods: 24, rate: 4.9 }));
    const withFee = calcInterest(input({ periods: 24, rate: 4.9, periodFeeRate: 0.3 }));
    expect(withFee.aprPercent).toBeGreaterThan(pure.aprPercent);
  });

  it("本金已全部由费用覆盖时无解，返回 null 不抛错", () => {
    const r = calcInterest(input({ upfrontFee: P }));
    expect(r.disbursed).toBe(0);
    expect(r.effectiveMonthlyRate).toBeNull();
    expect(r.aprPercent).toBeNull();
    expect(r.earPercent).toBeNull();
  });

  it("纯费用型借款也能解出年化（利率 0 且只有前置费用）", () => {
    const r = calcInterest(input({ rate: 0, periods: 12, upfrontFee: 1_200 }));
    expect(r.effectiveMonthlyRate).not.toBeNull();
    expect(r.aprPercent!).toBeGreaterThan(0);
  });

  it("利率与期限相同时，三种按月付息方式的真实年化彼此一致，到期一次还本付息明显更低", () => {
    // 12 万 / 30 年 / 名义年化 4.9%，无费用
    const base = { periods: 360, rate: 4.9 };
    const paying = METHODS.filter((m) => m !== "bullet").map(
      (m) => calcInterest(input({ ...base, method: m })).aprPercent!,
    );
    for (const apr of paying) expect(apr).toBeCloseTo(4.9, 3);

    // 到期一次还本付息把本金和 30 年利息全推到期末，占用资金时间最长 → 真实成本远低于报价
    const bullet = calcInterest(input({ ...base, method: "bullet" }));
    expect(bullet.aprPercent!).toBeLessThan(3.5);
    expect(bullet.totalInterest).toBeCloseTo(490 * 360, 2);
  });

  it("一旦按名义本金收每期费率，还款节奏本身会改变真实年化", () => {
    const aprs = METHODS.filter((m) => m !== "bullet").map(
      (m) => calcInterest(input({ periods: 360, method: m, periodFeeRate: 0.05 })).aprPercent!,
    );
    expect(new Set(aprs.map((a) => a.toFixed(2))).size).toBe(aprs.length);
  });
});
