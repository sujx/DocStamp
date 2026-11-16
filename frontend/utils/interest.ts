/**
 * 利息计算引擎——纯函数，零 Vue 依赖。
 *
 * 现金流骨架对所有还款方式统一：
 *   t=0  净流入 = 本金 − 一次性前置费用   （前置费用在此自动暴露砍头息）
 *   t=k  净流出 = 本期本息 + 本期分期费用
 * 还款方式只决定「本期本息」怎么摊；两种费用模型是正交叠加项。
 * 真实年化 = 对该现金流解 NPV = 0 的期利率，再分别按 APR / EAR 两种口径年化。
 */

export type RateUnit = "year" | "month" | "day"
export type RepayMethod = "annuity" | "linear" | "interest-first" | "bullet"

export interface InterestInput {
  /** 名义本金（元），也是还款与分期费率的计费基数 */
  principal: number
  /** 期数，一期 = 一个月 */
  periods: number
  /** 用户输入的利率数值，含义随 rateUnit 变 */
  rate: number
  /** day 单位按「万分之」计，与日息万 2 之类的报价一致 */
  rateUnit: RateUnit
  /** 一次性前置费用（元），从到手现金里扣，不减少还款基数 */
  upfrontFee: number
  /** 每期费率百分数，按名义本金收，不随余额衰减（信用卡分期式的手续费） */
  periodFeeRate: number
  method: RepayMethod
}

export interface ScheduleRow {
  period: number
  opening: number
  principalPart: number
  interestPart: number
  /** 本期本息和 */
  payment: number
  feePart: number
  /** 本期从口袋里出去的总额 = payment + feePart */
  outflow: number
  balance: number
}

export interface InterestResult {
  rows: ScheduleRow[]
  monthlyRate: number
  nominalAnnualPercent: number
  /** 到手现金 = 本金 − 一次性前置费用 */
  disbursed: number
  totalPrincipal: number
  totalInterest: number
  totalPeriodFee: number
  totalUpfrontFee: number
  totalFee: number
  totalRepayment: number
  totalOutflow: number
  /** 全成本 = 总利息 + 总费用 */
  totalCost: number
  firstPayment: number
  lastPayment: number
  effectiveMonthlyRate: number | null
  /** 期利率 × 12，与贷款报价同口径 */
  aprPercent: number | null
  /** (1 + 期利率) ^ 12 − 1，复利有效年利率 */
  earPercent: number | null
}

/** 计息年天数：日利率换年化时与「日息万 2 = 年化 7.3%」的报价口径对齐 */
const DAYS_PER_YEAR = 365
const PERIODS_PER_YEAR = 12

function cents(value: number): number {
  return Math.round(value * 100) / 100
}

export function toMonthlyRate(rate: number, unit: RateUnit): number {
  switch (unit) {
    case "year":
      return rate / 100 / PERIODS_PER_YEAR
    case "month":
      return rate / 100
    case "day":
      return (rate / 10_000) * (DAYS_PER_YEAR / PERIODS_PER_YEAR)
  }
}

export function toNominalAnnualPercent(rate: number, unit: RateUnit): number {
  switch (unit) {
    case "year":
      return rate
    case "month":
      return rate * PERIODS_PER_YEAR
    case "day":
      return (rate / 10_000) * DAYS_PER_YEAR * 100
  }
}

export function aprPercent(monthlyRate: number): number {
  return monthlyRate * PERIODS_PER_YEAR * 100
}

export function annualizeEarPercent(monthlyRate: number): number {
  return (Math.pow(1 + monthlyRate, PERIODS_PER_YEAR) - 1) * 100
}

/** 把利率百分数按还款方式摊成每期的本息与期末余额。 */
function amortize(
  principal: number,
  periods: number,
  monthlyRate: number,
  method: RepayMethod,
): Array<{ principalPart: number; interestPart: number; closing: number }> {
  const rows: Array<{ principalPart: number; interestPart: number; closing: number }> = []
  let balance = principal

  if (method === "interest-first") {
    const interest = cents(balance * monthlyRate)
    for (let k = 1; k <= periods; k++) {
      const principalPart = k === periods ? balance : 0
      balance = cents(balance - principalPart)
      rows.push({ principalPart, interestPart: interest, closing: balance })
    }
    return rows
  }

  if (method === "bullet") {
    const totalInterest = cents(principal * monthlyRate * periods)
    for (let k = 1; k <= periods; k++) {
      const last = k === periods
      rows.push({
        principalPart: last ? principal : 0,
        interestPart: last ? totalInterest : 0,
        closing: last ? 0 : principal,
      })
    }
    return rows
  }

  const fixedPrincipal = cents(principal / periods)
  const fixedPayment =
    monthlyRate === 0
      ? cents(principal / periods)
      : cents(
          (principal * monthlyRate * Math.pow(1 + monthlyRate, periods)) /
            (Math.pow(1 + monthlyRate, periods) - 1),
        )

  for (let k = 1; k <= periods; k++) {
    const interestPart = cents(balance * monthlyRate)
    // 末期补差，保证 Σ本金 恰等于名义本金、期末余额恰为 0
    const principalPart =
      k === periods
        ? balance
        : method === "linear"
          ? fixedPrincipal
          : cents(fixedPayment - interestPart)
    balance = cents(balance - principalPart)
    rows.push({ principalPart, interestPart, closing: balance })
  }
  return rows
}

export function npv(monthlyRate: number, inflow: number, outflows: number[]): number {
  let pv = 0
  for (let k = 0; k < outflows.length; k++) {
    pv += outflows[k]! / Math.pow(1 + monthlyRate, k + 1)
  }
  return inflow - pv
}

/**
 * 二分法解期利率。NPV 对期利率单调递增，符号一变即有根，故不需要牛顿法的初值猜测，
 * 也不会在一口价利率为 0 或费率极端时发散。
 */
export function irrMonthly(inflow: number, outflows: number[]): number | null {
  if (!(inflow > 0) || !outflows.some((o) => o > 0)) return null

  let lo = -0.99
  let hi = 10
  if (npv(lo, inflow, outflows) > 0 || npv(hi, inflow, outflows) < 0) return null

  for (let i = 0; i < 100; i++) {
    const mid = (lo + hi) / 2
    if (npv(mid, inflow, outflows) <= 0) lo = mid
    else hi = mid
  }
  return (lo + hi) / 2
}

export function calcInterest(raw: InterestInput): InterestResult {
  const principal = cents(raw.principal)
  const periods = Math.max(1, Math.floor(raw.periods))
  const monthlyRate = toMonthlyRate(raw.rate, raw.rateUnit)
  const upfrontFee = cents(raw.upfrontFee)
  const feePart = cents((principal * raw.periodFeeRate) / 100)

  const parts = amortize(principal, periods, monthlyRate, raw.method)
  const rows: ScheduleRow[] = []
  let opening = principal

  for (let k = 0; k < parts.length; k++) {
    const part = parts[k]!
    const payment = cents(part.principalPart + part.interestPart)
    rows.push({
      period: k + 1,
      opening,
      principalPart: part.principalPart,
      interestPart: part.interestPart,
      payment,
      feePart,
      outflow: cents(payment + feePart),
      balance: part.closing,
    })
    opening = part.closing
  }

  const totalRepayment = cents(rows.reduce((acc, row) => acc + row.payment, 0))
  const totalPeriodFee = cents(rows.reduce((acc, row) => acc + row.feePart, 0))
  const totalPrincipal = cents(rows.reduce((acc, row) => acc + row.principalPart, 0))
  const totalInterest = cents(totalRepayment - principal)
  const totalFee = cents(totalPeriodFee + upfrontFee)
  const totalOutflow = cents(totalRepayment + totalPeriodFee + upfrontFee)
  const disbursed = cents(principal - upfrontFee)

  const effectiveMonthlyRate = irrMonthly(
    disbursed,
    rows.map((row) => row.outflow),
  )

  return {
    rows,
    monthlyRate,
    nominalAnnualPercent: toNominalAnnualPercent(raw.rate, raw.rateUnit),
    disbursed,
    totalPrincipal,
    totalInterest,
    totalPeriodFee,
    totalUpfrontFee: upfrontFee,
    totalFee,
    totalRepayment,
    totalOutflow,
    totalCost: cents(totalOutflow - principal),
    firstPayment: rows[0]!.payment,
    lastPayment: rows[rows.length - 1]!.payment,
    effectiveMonthlyRate,
    aprPercent: effectiveMonthlyRate === null ? null : aprPercent(effectiveMonthlyRate),
    earPercent: effectiveMonthlyRate === null ? null : annualizeEarPercent(effectiveMonthlyRate),
  }
}
