<template>
  <div>
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">
      <!-- 输入 -->
      <UCard class="xl:col-span-1">
        <template #header>
          <h2 class="text-[15px] font-medium text-primary">{{ $t("interestCalc.form.title") }}</h2>
        </template>

        <UFormGroup class="mb-5" :label="$t('interestCalc.form.principal')" :error="fieldError('principal')">
          <UInput v-model="form.principal" type="number" min="0" inputmode="decimal">
            <template #trailing><span class="text-sm text-tertiary">{{ $t("interestCalc.form.yuan") }}</span></template>
          </UInput>
        </UFormGroup>

        <UFormGroup class="mb-5" :label="$t('interestCalc.form.period')" :error="fieldError('periodValue')">
          <div class="flex gap-2">
            <UInput v-model="form.periodValue" class="flex-1" type="number" min="0" inputmode="decimal" />
            <USelect v-model="form.periodUnit" :options="periodUnitOptions" class="w-24" />
          </div>
          <p class="text-xs text-tertiary mt-1">{{ $t("interestCalc.form.periodHint", { n: periods }) }}</p>
        </UFormGroup>

        <UFormGroup class="mb-5" :label="$t('interestCalc.form.rate')" :error="fieldError('rate')">
          <div class="flex gap-2">
            <UInput v-model="form.rate" class="flex-1" type="number" min="0" step="0.01" inputmode="decimal" />
            <USelect v-model="form.rateUnit" :options="rateUnitOptions" class="w-40" />
          </div>
        </UFormGroup>

        <UFormGroup class="mb-5" :label="$t('interestCalc.form.upfrontFee')" :error="fieldError('upfrontFee')">
          <UInput v-model="form.upfrontFee" type="number" min="0" inputmode="decimal" :placeholder="$t('interestCalc.form.optional')">
            <template #trailing><span class="text-sm text-tertiary">{{ $t("interestCalc.form.yuan") }}</span></template>
          </UInput>
          <p class="text-xs text-tertiary mt-1">{{ $t("interestCalc.form.upfrontFeeHint") }}</p>
        </UFormGroup>

        <UFormGroup class="mb-5" :label="$t('interestCalc.form.periodFeeRate')" :error="fieldError('periodFeeRate')">
          <UInput v-model="form.periodFeeRate" type="number" min="0" step="0.01" inputmode="decimal" :placeholder="$t('interestCalc.form.optional')">
            <template #trailing><span class="text-sm text-tertiary">%</span></template>
          </UInput>
          <p class="text-xs text-tertiary mt-1">{{ $t("interestCalc.form.periodFeeRateHint") }}</p>
        </UFormGroup>

        <fieldset>
          <legend class="text-sm font-medium text-primary mb-2">{{ $t("interestCalc.form.method") }}</legend>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="option in METHOD_OPTIONS"
              :key="option.value"
              type="button"
              class="method-item min-h-[44px]"
              :class="{ active: form.method === option.value }"
              :aria-pressed="form.method === option.value"
              @click="form.method = option.value"
            >
              {{ $t(option.labelKey) }}
            </button>
          </div>
        </fieldset>

        <UButton class="mt-5 min-h-[44px]" color="primary" variant="outline" @click="reset">
          {{ $t("interestCalc.form.reset") }}
        </UButton>
      </UCard>

      <!-- 结果 -->
      <div class="xl:col-span-2 space-y-6">
        <InterestSummaryCards v-if="result" :result="result" />
        <InterestMethodCompare
          v-if="result"
          :comparisons="comparisons"
          :current-method="form.method"
        />
        <InterestScheduleTable v-if="result" :rows="result.rows" />

        <p v-if="!isValid" class="text-sm text-secondary">
          {{ $t("interestCalc.form.fixErrors") }}
        </p>

        <p class="text-xs text-tertiary leading-relaxed">{{ $t("interestCalc.privacy") }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
  METHOD_OPTIONS,
  PERIOD_UNIT_OPTIONS,
  RATE_UNIT_OPTIONS,
  toPeriods,
  useInterestCalc,
} from "~/composables/useInterestCalc";

const { t } = useI18n();

const { form, errors, isValid, result, comparisons, reset } = useInterestCalc();

const periods = computed(() => toPeriods(form));

const periodUnitOptions = computed(() =>
  PERIOD_UNIT_OPTIONS.map((option) => ({ value: option.value, label: t(option.labelKey) })),
);

const rateUnitOptions = computed(() =>
  RATE_UNIT_OPTIONS.map((option) => ({ value: option.value, label: t(option.labelKey) })),
);

function fieldError(field: "principal" | "periodValue" | "rate" | "upfrontFee" | "periodFeeRate") {
  const key = errors.value[field];
  return key ? t(key) : undefined;
}
</script>

<style scoped>
.method-item {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 10px;
  background: var(--color-muted);
  border: 1px solid var(--color-border-default);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text-secondary);
  transition: background-color 0.15s, border-color 0.15s, color 0.15s;
}

.method-item:hover {
  background: var(--color-brand-soft);
}

.method-item.active {
  background: var(--color-brand-soft);
  border-color: var(--color-brand-500);
  color: var(--color-brand-700);
  font-weight: 600;
}
</style>
