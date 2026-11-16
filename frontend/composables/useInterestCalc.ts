import { computed, reactive } from "vue"
import {
  calcInterest,
  toNominalAnnualPercent,
  type InterestInput,
  type InterestResult,
  type RateUnit,
  type RepayMethod,
} from "~/utils/interest"

/** 一期 = 一个月，600 期 = 50 年，够覆盖任何合法房贷。 */
export const MAX_PERIODS = 600
const MAX_PRINCIPAL = 1_000_000_000
/** 名义年化上限 100%，超过就是输入错位（把月利率当年利率填了）。 */
const MAX_ANNUAL_PERCENT = 100
/** 每期费率上限 5%，换算成年是 60%，已经超出任何正规报价。 */
const MAX_PERIOD_FEE_RATE = 5

/** 数值字段由 `UInput type="number"` 写入，运行时会同时出现 string / number / null。 */
export type NumericField = string | number | null

export interface InterestForm {
  principal: NumericField
  periodValue: NumericField
  periodUnit: "year" | "month"
  rate: NumericField
  rateUnit: RateUnit
  upfrontFee: NumericField
  periodFeeRate: NumericField
  method: RepayMethod
}

export const METHOD_OPTIONS: Array<{ value: RepayMethod; labelKey: string }> = [
  { value: "annuity", labelKey: "interestCalc.method.annuity" },
  { value: "linear", labelKey: "interestCalc.method.linear" },
  { value: "interest-first", labelKey: "interestCalc.method.interestFirst" },
  { value: "bullet", labelKey: "interestCalc.method.bullet" },
]

export const RATE_UNIT_OPTIONS: Array<{ value: RateUnit; labelKey: string }> = [
  { value: "year", labelKey: "interestCalc.rateUnit.year" },
  { value: "month", labelKey: "interestCalc.rateUnit.month" },
  { value: "day", labelKey: "interestCalc.rateUnit.day" },
]

export const PERIOD_UNIT_OPTIONS: Array<{ value: "year" | "month"; labelKey: string }> = [
  { value: "year", labelKey: "interestCalc.periodUnit.year" },
  { value: "month", labelKey: "interestCalc.periodUnit.month" },
]

/**
 * `UInput type="number"` 交回来的是 number，删空时是 null，不是字符串。
 * 三种都得接住——早先无条件 `.trim()` 会在第一次键入时抛错。
 */
function num(value: string | number | null): number | null {
  if (value === null) return null
  if (typeof value === "string" && value.trim() === "") return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function createDefaultForm(): InterestForm {
  return {
    principal: "1000000",
    periodValue: "30",
    periodUnit: "year",
    rate: "4.9",
    rateUnit: "year",
    upfrontFee: "",
    periodFeeRate: "",
    method: "annuity",
  }
}

/** 期限统一折算成月数；按年填时四舍五入，容忍「29.5 年」这类写法。 */
export function toPeriods(form: InterestForm): number {
  const value = num(form.periodValue)
  if (value === null) return 0
  return Math.round(form.periodUnit === "year" ? value * 12 : value)
}

export function toInterestInput(form: InterestForm): InterestInput {
  return {
    principal: num(form.principal) ?? 0,
    periods: toPeriods(form),
    rate: num(form.rate) ?? 0,
    rateUnit: form.rateUnit,
    upfrontFee: num(form.upfrontFee) ?? 0,
    periodFeeRate: num(form.periodFeeRate) ?? 0,
    method: form.method,
  }
}

/**
 * 返回 字段 → 文案键。校验放在纯函数里，UI 只负责把键交给 $t。
 */
export function validateForm(form: InterestForm): Partial<Record<keyof InterestForm, string>> {
  const errors: Partial<Record<keyof InterestForm, string>> = {}

  const principal = num(form.principal)
  if (principal === null || principal <= 0 || principal > MAX_PRINCIPAL) {
    errors.principal = "interestCalc.error.principal"
  }

  const periods = toPeriods(form)
  if (periods < 1 || periods > MAX_PERIODS) {
    errors.periodValue = "interestCalc.error.periods"
  }

  const rate = num(form.rate) ?? 0
  const annualPercent = toNominalAnnualPercent(rate, form.rateUnit)
  if (rate < 0 || annualPercent > MAX_ANNUAL_PERCENT) {
    errors.rate = "interestCalc.error.rate"
  }

  const upfrontFee = num(form.upfrontFee) ?? 0
  if (upfrontFee < 0 || (principal !== null && upfrontFee >= principal)) {
    errors.upfrontFee = "interestCalc.error.upfrontFee"
  }

  const feeRate = num(form.periodFeeRate) ?? 0
  if (feeRate < 0 || feeRate > MAX_PERIOD_FEE_RATE) {
    errors.periodFeeRate = "interestCalc.error.feeRate"
  }

  return errors
}

export function formatAmount(value: number, locale: string): string {
  return new Intl.NumberFormat(locale === "en" ? "en-US" : "zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatPercent(value: number | null, digits = 2): string {
  if (value === null) return "—"
  return `${value.toFixed(digits)}%`
}

export interface MethodComparison {
  method: RepayMethod
  labelKey: string
  result: InterestResult
}

export function useInterestCalc() {
  const form = reactive<InterestForm>(createDefaultForm())

  const errors = computed(() => validateForm(form))
  const isValid = computed(() => Object.keys(errors.value).length === 0)

  const result = computed<InterestResult | null>(() =>
    isValid.value ? calcInterest(toInterestInput(form)) : null,
  )

  // 多方案对比 = 同一份输入换四种还款方式，口径完全一致才可比
  const comparisons = computed<MethodComparison[]>(() => {
    if (!isValid.value) return []
    const base = toInterestInput(form)
    return METHOD_OPTIONS.map((option) => ({
      method: option.value,
      labelKey: option.labelKey,
      result: calcInterest({ ...base, method: option.value }),
    }))
  })

  function reset() {
    Object.assign(form, createDefaultForm())
  }

  return { form, errors, isValid, result, comparisons, reset }
}
