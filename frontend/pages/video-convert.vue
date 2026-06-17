<template>
  <div class="max-w-5xl mx-auto px-6 py-8">
    <PageHeader :title="$t('videoConvert.title')" :description="$t('videoConvert.description')" />
    <VideoConvertPanel />
  </div>
</template>

<script setup lang="ts">
const VideoConvertPanel = defineAsyncComponent(() => import("~/components/VideoConvertPanel.vue"));
</script>
