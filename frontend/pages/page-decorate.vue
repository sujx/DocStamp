<template>
  <div class="max-w-5xl mx-auto px-6 py-8">
    <PageHeader :title="$t('pageDecorate.title')" :description="$t('pageDecorate.description')" />
    <PageDecoratePanel />
  </div>
</template>

<script setup lang="ts">
const PageDecoratePanel = defineAsyncComponent(() => import("~/components/PageDecoratePanel.vue"));
</script>
