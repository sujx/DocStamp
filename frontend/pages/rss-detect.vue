<template>
  <div class="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
    <PageHeader :title="$t('rssDetect.title')" :description="$t('rssDetect.description')" />
    <RssDetectPanel />
  </div>
</template>

<script setup lang="ts">
import RssDetectPanel from "~/components/RssDetectPanel.vue";
</script>
