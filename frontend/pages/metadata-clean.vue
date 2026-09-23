<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <PageHeader :title="$t('metadataClean.title')" :description="$t('metadataClean.description')" />
    <MetadataCleanTab />
  </div>
</template>

<script setup lang="ts">
import MetadataCleanTab from "~/components/MetadataCleanTab.vue";
</script>
