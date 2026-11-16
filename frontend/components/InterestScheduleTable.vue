<template>
  <UCard>
    <template #header>
      <div>
        <h2 class="text-lg font-semibold text-primary">{{ t("interestCalc.table.title") }}</h2>
        <p class="text-sm text-secondary mt-1">
          {{ t("interestCalc.table.subtitle", { n: rows.length }) }}
        </p>
      </div>
    </template>

    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <caption class="sr-only">{{ t("interestCalc.table.title") }}</caption>
        <thead>
          <tr class="text-xs text-tertiary border-b border-default">
            <th v-for="col in columns" :key="col.labelKey" scope="col" class="font-medium py-2 pr-3 text-right first:text-left">
              {{ t(col.labelKey) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in visibleRows"
            :key="row.period"
            class="border-b border-subtle last:border-0 tabular-nums"
          >
            <th scope="row" class="py-2 pr-3 text-left font-medium text-primary">{{ row.period }}</th>
            <td class="py-2 pr-3 text-right text-secondary">{{ money(row.opening) }}</td>
            <td class="py-2 pr-3 text-right text-primary">{{ money(row.principalPart) }}</td>
            <td class="py-2 pr-3 text-right text-primary">{{ money(row.interestPart) }}</td>
            <td class="py-2 pr-3 text-right text-primary">{{ money(row.feePart) }}</td>
            <td class="py-2 pr-3 text-right text-primary">{{ money(row.outflow) }}</td>
            <td class="py-2 pr-3 text-right text-secondary">{{ money(row.balance) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <UButton
      v-if="rows.length > COLLAPSED_COUNT"
      class="mt-4 min-h-[44px]"
      color="primary"
      variant="outline"
      @click="expanded = !expanded"
    >
      {{ expanded ? t("interestCalc.table.collapse") : t("interestCalc.table.expand", { n: rows.length }) }}
    </UButton>
  </UCard>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { ScheduleRow } from "~/utils/interest";
import { formatAmount } from "~/composables/useInterestCalc";

const props = defineProps<{ rows: ScheduleRow[] }>();

const { t, locale } = useI18n();

// 30 年房贷有 360 行，默认只铺前 12 期 + 末期，否则页面本身就是个性能问题
const COLLAPSED_COUNT = 12;
const expanded = ref(false);

const columns = [
  { labelKey: "interestCalc.table.period" },
  { labelKey: "interestCalc.table.opening" },
  { labelKey: "interestCalc.table.principalPart" },
  { labelKey: "interestCalc.table.interestPart" },
  { labelKey: "interestCalc.table.feePart" },
  { labelKey: "interestCalc.table.outflow" },
  { labelKey: "interestCalc.table.balance" },
];

const visibleRows = computed(() => {
  if (expanded.value || props.rows.length <= COLLAPSED_COUNT + 1) return props.rows;
  return [...props.rows.slice(0, COLLAPSED_COUNT), props.rows[props.rows.length - 1]!];
});

function money(value: number) {
  return formatAmount(value, locale.value);
}
</script>
