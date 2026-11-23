<template>
  <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
    <PageHeader :title="$t('interestCalc.title')" :description="$t('interestCalc.description')" />
    <InterestCalcPanel />
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n();

useHead({
  title: computed(() => t("interestCalc.metaTitle")),
  meta: [{ name: "description", content: computed(() => t("interestCalc.metaDescription")) }],
});
</script>
