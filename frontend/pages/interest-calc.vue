<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
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
