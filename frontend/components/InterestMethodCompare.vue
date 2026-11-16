<template>
  <UCard v-if="comparisons.length">
    <template #header>
      <div>
        <h2 class="text-lg font-semibold text-primary">{{ t("interestCalc.compare.title") }}</h2>
        <p class="text-sm text-secondary mt-1">{{ t("interestCalc.compare.subtitle") }}</p>
      </div>
    </template>

    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <caption class="sr-only">{{ t("interestCalc.compare.title") }}</caption>
        <thead>
          <tr class="text-xs text-tertiary border-b border-default">
            <th scope="col" class="font-medium py-2 pr-3 text-left">{{ t("interestCalc.compare.method") }}</th>
            <th v-for="col in columns" :key="col.labelKey" scope="col" class="font-medium py-2 pr-3 text-right">
              {{ t(col.labelKey) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in comparisons"
            :key="item.method"
            class="border-b border-subtle last:border-0 tabular-nums"
            :class="{ 'row-current': item.method === currentMethod }"
          >
            <th scope="row" class="py-2 pr-3 text-left font-medium text-primary">
              {{ t(item.labelKey) }}
              <span v-if="item.method === currentMethod" class="badge-current">
                {{ t("interestCalc.compare.current") }}
              </span>
            </th>
            <td class="py-2 pr-3 text-right text-primary">{{ perPeriod(item.result) }}</td>
            <td class="py-2 pr-3 text-right text-primary">{{ amount(item.result.totalInterest) }}</td>
            <td class="py-2 pr-3 text-right text-primary">{{ amount(item.result.totalFee) }}</td>
            <td class="py-2 pr-3 text-right text-primary">{{ amount(item.result.totalCost) }}</td>
            <td class="py-2 pr-3 text-right font-semibold text-brand-700">
              {{ formatPercent(item.result.aprPercent) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p class="text-xs text-tertiary mt-3">{{ t("interestCalc.compare.hint") }}</p>
  </UCard>
</template>

<script setup lang="ts">
import type { InterestResult, RepayMethod } from "~/utils/interest";
import { formatAmount, formatPercent, type MethodComparison } from "~/composables/useInterestCalc";

const props = defineProps<{
  comparisons: MethodComparison[];
  currentMethod: RepayMethod;
}>();

const { t, locale } = useI18n();

const columns = [
  { labelKey: "interestCalc.compare.perPeriod" },
  { labelKey: "interestCalc.compare.totalInterest" },
  { labelKey: "interestCalc.compare.totalFee" },
  { labelKey: "interestCalc.compare.totalCost" },
  { labelKey: "interestCalc.compare.apr" },
];

// 等额本金与到期一次还本付息的每期金额不等，取首期并标注区间终点
function perPeriod(result: InterestResult) {
  const { firstPayment, lastPayment } = result;
  const first = formatAmount(firstPayment, locale.value);
  if (firstPayment === lastPayment) return first;
  return `${first} → ${formatAmount(lastPayment, locale.value)}`;
}

function amount(value: number) {
  return formatAmount(value, locale.value);
}
</script>

<style scoped>
.row-current {
  background: var(--color-brand-soft);
}

.badge-current {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 9999px;
  background: var(--color-brand-100);
  color: var(--color-brand-700);
  font-size: 11px;
  font-weight: 500;
  vertical-align: middle;
}
</style>
