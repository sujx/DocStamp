<template>
  <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
    <PageHeader :title="$t('pdfRedact.title')" :description="$t('pdfRedact.description')" />
    <PdfRedactTab />
    <NuxtLink
      to="/guide/pdf-redact"
      class="mt-6 inline-flex min-h-[44px] items-center text-sm text-brand-600 no-underline transition-colors hover:underline"
    >{{ $t("pdfRedact.guideLink") }}</NuxtLink>
  </div>
</template>

<script setup lang="ts">
import PdfRedactTab from "~/components/PdfRedactTab.vue";
</script>
