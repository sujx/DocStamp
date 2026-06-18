<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('pdf-tools.title')" :description="$t('pdf-tools.description')" />
    <UTabs :items="tabs" class="mb-6">
      <template #text><PdfToTextPanel /></template>
      <template #compress><PdfCompressPanel /></template>
      <template #decorate><PageDecoratePanel /></template>
    </UTabs>
  </div>
</template>

<script setup lang="ts">
// Lazy-load tab panels to avoid loading all tool code at once
const PdfToTextPanel = defineAsyncComponent(() => import("~/components/PdfToTextPanel.vue"));
const PdfCompressPanel = defineAsyncComponent(() => import("~/components/PdfCompressPanel.vue"));
const PageDecoratePanel = defineAsyncComponent(() => import("~/components/PageDecoratePanel.vue"));

const { t } = useI18n();
const tabs = computed(() => [
  { label: t("tabs.pdfToText"), slot: "text" },
  { label: t("tabs.pdfCompress"), slot: "compress" },
  { label: t("tabs.pageDecorate"), slot: "decorate" },
]);
</script>
