<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('rssDetect.title')" :description="$t('rssDetect.description')" />
    <RssDetectPanel />
  </div>
</template>

<script setup lang="ts">
import RssDetectPanel from "~/components/RssDetectPanel.vue";
</script>
