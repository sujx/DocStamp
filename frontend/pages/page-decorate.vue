<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('pageDecorate.title')" :description="$t('pageDecorate.description')" />
    <PageDecoratePanel />
  </div>
</template>

<script setup lang="ts">
import PageDecoratePanel from "~/components/PageDecoratePanel.vue";
</script>
