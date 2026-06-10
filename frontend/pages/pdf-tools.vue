<template>
  <div class="max-w-3xl mx-auto px-6 py-8">
    <PageHeader :title="$t('pdfTools2.title')" :description="$t('pdfTools2.description')" />
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
