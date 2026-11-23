<template>
  <div class="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
    <PageHeader :title="$t('metadataClean.title')" :description="$t('metadataClean.description')" />
    <MetadataCleanTab />
  </div>
</template>

<script setup lang="ts">
import MetadataCleanTab from "~/components/MetadataCleanTab.vue";
</script>
