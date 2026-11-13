<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('pdfRedact.title')" :description="$t('pdfRedact.description')" />
    <PdfRedactTab />
    <NuxtLink
      to="/guide/pdf-redact"
      class="mt-6 inline-flex min-h-[44px] items-center text-sm text-brand-600 no-underline transition-colors duration-150 hover:underline"
    >{{ $t("pdfRedact.guideLink") }}</NuxtLink>
  </div>
</template>

<script setup lang="ts">
import PdfRedactTab from "~/components/PdfRedactTab.vue";
</script>
