<template>
  <div class="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
    <PageHeader :title="$t('pageDecorate.title')" :description="$t('pageDecorate.description')" />
    <PageDecoratePanel />
  </div>
</template>

<script setup lang="ts">
import PageDecoratePanel from "~/components/PageDecoratePanel.vue";
</script>
