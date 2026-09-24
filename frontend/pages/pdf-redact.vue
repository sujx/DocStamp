<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('pdfRedact.title')" :description="$t('pdfRedact.description')" />
    <PdfRedactTab />
  </div>
</template>

<script setup lang="ts">
import PdfRedactTab from "~/components/PdfRedactTab.vue";
</script>
