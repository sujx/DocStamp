<template>
  <div class="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
    <PageHeader :title="$t('pdfToText.title')" :description="$t('pdfToText.description')" />
    <PdfToTextPanel />
  </div>
</template>

<script setup lang="ts">
import PdfToTextPanel from "~/components/PdfToTextPanel.vue";
</script>
