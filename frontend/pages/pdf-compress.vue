<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('pdfCompress.title')" :description="$t('pdfCompress.description')" />
    <PdfCompressPanel />
  </div>
</template>

<script setup lang="ts">
import PdfCompressPanel from "~/components/PdfCompressPanel.vue";
</script>
