<template>
  <div class="max-w-5xl mx-auto px-6 py-8">
    <PageHeader />
    <UTabs :items="tabItems" class="mb-6">
      <template #props><PropertiesTab /></template>
      <template #clean><MetadataCleanTab /></template>
    </UTabs>
  </div>
</template>

<script setup lang="ts">
import MetadataCleanTab from "~/components/MetadataCleanTab.vue";

const { t } = useI18n();
const tabItems = computed(() => [
  { label: t("tabs.properties"), slot: "props" },
  { label: t("tabs.metadataClean"), slot: "clean" },
]);
</script>
