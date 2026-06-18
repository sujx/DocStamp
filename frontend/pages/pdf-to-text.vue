<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('pdfToText.title')" :description="$t('pdfToText.description')" />
    <PdfToTextPanel />
  </div>
</template>

<script setup lang="ts">
const PdfToTextPanel = defineAsyncComponent(() => import("~/components/PdfToTextPanel.vue"));
</script>
