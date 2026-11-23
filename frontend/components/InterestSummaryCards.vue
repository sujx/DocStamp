<template>
  <UCard>
    <template #header>
      <div>
        <h2 class="text-[15px] font-medium text-primary">{{ t("interestCalc.result.title") }}</h2>
        <p class="text-sm text-secondary mt-1">{{ t("interestCalc.result.subtitle") }}</p>
      </div>
    </template>

    <!-- 主答案：真实年化。APR 与贷款报价同口径，EAR 给出复利后的真实负担 -->
    <div class="rate-band">
      <div class="flex-1 min-w-0">
        <p class="text-sm text-secondary">{{ t("interestCalc.result.apr") }}</p>
        <p class="rate-figure">{{ formatPercent(result.aprPercent) }}</p>
        <p class="text-xs text-tertiary mt-1">
          {{ t("interestCalc.result.aprHint", { nominal: formatPercent(result.nominalAnnualPercent) }) }}
        </p>
      </div>
      <div class="text-right shrink-0">
        <p class="text-sm text-secondary">{{ t("interestCalc.result.ear") }}</p>
        <p class="text-[28px] font-medium tabular-nums text-primary">{{ formatPercent(result.earPercent) }}</p>
        <p class="text-xs text-tertiary mt-1">{{ t("interestCalc.result.earHint") }}</p>
      </div>
    </div>

    <p v-if="result.aprPercent === null" class="text-sm text-secondary mt-3">
      {{ t("interestCalc.result.notApplicable") }}
    </p>

    <dl class="grid grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-5 mt-6">
      <div v-for="tile in tiles" :key="tile.labelKey">
        <dt class="text-xs text-tertiary">{{ t(tile.labelKey) }}</dt>
        <dd class="mt-0.5 text-[20px] font-medium tabular-nums text-primary">{{ tile.value }}</dd>
        <dd v-if="tile.hint" class="text-xs text-tertiary mt-0.5">{{ tile.hint }}</dd>
      </div>
    </dl>
  </UCard>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { InterestResult } from "~/utils/interest";
import { formatAmount, formatPercent } from "~/composables/useInterestCalc";

const props = defineProps<{ result: InterestResult }>();

const { t, locale } = useI18n();

function money(value: number) {
  return formatAmount(value, locale.value);
}

// 每期金额只有不相同时才并列两个数，等额本息与先息后本读起来更干净
const paymentValue = computed(() => {
  const { firstPayment, lastPayment } = props.result;
  if (firstPayment === lastPayment) return money(firstPayment);
  return `${money(firstPayment)} → ${money(lastPayment)}`;
});

const tiles = computed(() => [
  {
    labelKey: "interestCalc.result.disbursed",
    value: money(props.result.disbursed),
    hint:
      props.result.totalUpfrontFee > 0
        ? `${money(props.result.totalPrincipal)} − ${money(props.result.totalUpfrontFee)}`
        : undefined,
  },
  {
    labelKey: "interestCalc.result.perPeriod",
    value: paymentValue.value,
    hint: undefined,
  },
  {
    labelKey: "interestCalc.result.totalOutflow",
    value: money(props.result.totalOutflow),
    hint: undefined,
  },
  {
    labelKey: "interestCalc.result.totalInterest",
    value: money(props.result.totalInterest),
    hint: undefined,
  },
  {
    labelKey: "interestCalc.result.totalFee",
    value: money(props.result.totalFee),
    hint: t("interestCalc.result.feeSplit", {
      period: money(props.result.totalPeriodFee),
      upfront: money(props.result.totalUpfrontFee),
    }),
  },
  {
    labelKey: "interestCalc.result.totalCost",
    value: money(props.result.totalCost),
    hint: t("interestCalc.result.totalCostHint"),
  },
]);
</script>

<style scoped>
.rate-band {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  background: var(--color-brand-soft);
  border: 1px solid var(--color-brand-500);
  border-radius: 10px;
}

.rate-figure {
  font-size: 32px;
  line-height: 1.15;
  font-weight: 500;
  color: var(--color-brand-700);
  font-variant-numeric: tabular-nums;
}
</style>
